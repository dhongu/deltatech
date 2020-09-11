#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <time.h>
#include <algorithm>


#ifdef SAPonNT
#include <direct.h>
#include <process.h>
#include <windows.h>
#include <tchar.h>
#else
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>
#endif

#ifdef SAPwithPASE400
	#include "as4exec.h"
	#define SAPUCX_H
#endif
#include "rfcexec.h"

#ifdef SAPonOS400
	#include <spawn.h>

	#ifdef SAPwithCHAR_EBCDIC
	#include <qp0z1170.h>     // weil’s der CPP Compiler im Gegensatz zum C Compiler für GetEnvironU braucht
	#endif

	externC int o4_convert_environ_a(void);
	DECLAREenvironU;
#endif
#if defined(SAPonOS400)
	/* o4fprintfU, o4fgetsU
	 * calling o4xxxU instead of xxxU produces much smaller code,
	 * because it directly expands to xxxU16, while xxxU expands to
	 * as4_xxx  which links against the whole pipe check and handling for ILE.
     * This creates an executable containing almost the whole platform 
	 * specific kernel and needs the ILE O4PRTLIB in a special library.
	 * Because we have no pipe usage of fxxxU here I use o4xxxU.
	 * ATTENTION:
	 * In any case the above mentioned functions are efectively used for 
	 * pipes, the redefinition below corrupts this functionality
	 * because than the pipe handling is not called for our platform.
	 */
	#undef fprintfU
	#define fprintfU o4fprintfU
	#undef fgetsU
	#define fgetsU o4fgetsU
#endif

#ifdef SAPonNT
#    ifndef pclose
#        define pclose _pclose
#    endif
#endif

#define ERROR_MESSAGE_SIZE 511

/**
 * \ingroup rfcexec
 *
 * \version 1.0
 * First version of rfcexec program. Only RFC_REMOTE_EXEC is implemented.
 *
 * \date 02-25-2008
 *
 * \author d029216
 */

RFC_FUNCTION_DESC_HANDLE RfcExecServer::rfc_exec;
RFC_FUNCTION_DESC_HANDLE RfcExecServer::rfc_pipe;

RfcExecServer* theServer = NULL;

class StrCmp
{
public:
    StrCmp(SAP_UC* str1) : str1(str1) {}
    bool operator()(const SAP_UC* str2)
    {
        return strcmpU(str1, str2) == 0;
    }
private:
    SAP_UC* str1;
};

/**
 * \brief  Callback function for the RFC SDK.
 * \ingroup rfcexec
 *
 * This is the "bridge" between the C RFC SDK and the C++ rfcexec program. If there will be more
 * than one parallel connection, then at this point instead of "theServer" we'll need either a kind
 * of hashmap mapping the RFC_CONNECTION_HANDLEs to the corresponding RfcExecServer objects, or
 * we'll need to use TLS like JCo 2.1.
 *
 * Whenever an RFC request for the FM RFC_REMOTE_EXEC arrives from the backend, this function is
 * triggered.
 *
 * \in rfcHandle RFC connection over which the request came in.
 * \in funcHandle Data container for the inputs/outputs of the FM.
 * \out *errorInfo Returns detailed error information to the backend, in case anything goes wrong or access is denied.
 * \return RFC_OK, if everything went fine. RFC_EXTERNAL_FAILURE, if the parameters could not be read, access is
 * denied or the creation of the child process failed.
 */
extern "C" RFC_RC SAP_API RFC_REMOTE_EXEC(RFC_CONNECTION_HANDLE rfcHandle, RFC_FUNCTION_HANDLE funcHandle, RFC_ERROR_INFO *errorInfo){
	return theServer->handleRequest(rfcHandle, funcHandle, errorInfo);
}

/**
 * \brief  Implementation of the "function module" RFC_REMOTE_EXEC.
 * \ingroup rfcexec
 *
 * Whenever an RFC request for the FM RFC_REMOTE_EXEC arrives from the backend, this function is
 * triggered and checks, whether the current user has authorization to execute the given OS command.
 * If access is granted, the command is executed in an asynchronous child process.
 * \note For performance reasons ALE doesn't want to wait for error/success output of the process,
 * therefore the PIPEDATA table is not used in this implementation.
 *
 * \in rfcHandle RFC connection over which the request came in.
 * \in funcHandle Data container for the inputs/outputs of the FM.
 * \out *errorInfo Returns detailed error information to the backend, in case anything goes wrong or access is denied.
 * \return RFC_OK, if everything went fine. RFC_EXTERNAL_FAILURE, if the parameters could not be read, access is
 * denied or the creation of the child process failed.
 */
RFC_RC RfcExecServer::handleRequest(RFC_CONNECTION_HANDLE rfcHandle, RFC_FUNCTION_HANDLE funcHandle, RFC_ERROR_INFO *errorInfo){
	RFC_RC rc = RFC_OK;
	RFC_ATTRIBUTES attributes;
	SAP_UC command[256] = iU("");
	SAP_UC readPipe[2] = iU("");

	rc = RfcGetConnectionAttributes(rfcHandle, &attributes, errorInfo);
	if (rc != RFC_OK){
		trace(cU("Reading Attributes failed"), errorInfo->message, 1);
		return RFC_EXTERNAL_FAILURE;
	}

	if (attributes.trace[0] != cU('0')){
		if (traceFile == NULL){
			openTrace();
			trace(cU("Tracing turned on on backend's request"), NULL);
			printTraceHeader();
			backendRequestedTrace = true;
		}
	}
	else if(backendRequestedTrace){
		backendRequestedTrace = false;
		trace(cU("Tracing turned off on backend's request"), NULL);
		closeTrace();
	}
	trace(cU("Received call for"), cU("RFC_REMOTE_EXEC"));

	rc = RfcGetString(funcHandle, cU("COMMAND"), command, sizeofU(command), NULL, errorInfo);
	if (rc != RFC_OK){
		trace(cU("Reading COMMAND value failed"), errorInfo->message, 1);
		return RFC_EXTERNAL_FAILURE;
	}
	RfcGetString(funcHandle, cU("READ"), readPipe, sizeofU(readPipe), NULL, NULL);

	if (!checkAuthorization(attributes.user, attributes.sysId, attributes.client, command, attributes.progName)){
		/*CCQ_SECURE_LIB_OK*/
		sprintfU(errorInfo->message, cU("Access denied"));
		trace(cU("Access was denied"), NULL, 1);
		return RFC_EXTERNAL_FAILURE;
	}

#ifdef SAPonOS400
	SAP_UC** args;
	int numArgs = 1;
	bool inArg = false;
	pid_t pid;
	inheritance_t inherit;
	size_t len, i;

	len = strlenU(command);
	for (i=0; i<len; i++){
		switch(command[i]){
			case cU('"'): inArg = !inArg; break;
			case cU(' '): if (inArg) continue;
				numArgs++;
				command[i] = cU('\0');
				break;
		}
	}
	args = new SAP_UC*[numArgs+1];
	args[0] = command;
	numArgs = 1;
	for (i=0; i<len; i++){
		if (command[i] == cU('\0')){
			args[numArgs++] = command+(i+1);
			trace(cU("args parameter"), command+(i+1), 2);
		}
	}
	args[numArgs] = NULL;

	if (traceFile){
		SAP_UC numVal[16];
		/*CCQ_SECURE_LIB_OK*/
		sprintfU(numVal, cU("%d"), numArgs-1);
		trace(cU("Number of arguments"), numVal, 1);
	}

	if (getenvU(cU("PATH")) == NULL)
		putenvU(cU("PATH=%LIBL%:"));
	trace(cU("Using PATH"), getenvU(cU("PATH")), 1);

	inherit.flags = 0;  /* initialize inheritance structure */
	inherit.pgroup = SPAWN_NEWPGROUP;

	GETenvironU;
	if (environU == NULL){
		SAP_UC* envvar_array[1] = { NULL };
		pid = spawnU(command, 0, NULL, &inherit, args, envvar_array);
	}
	else{
		pid = spawnU(command, 0, NULL, &inherit, args, environU);
	}

	delete[] args;
	if (pid == -1) {
        /*CCQ_SECURE_LIB_OK*/
		strncpyU(errorInfo->message, strerrorU(errno), ERROR_MESSAGE_SIZE);
		errorInfo->message[ERROR_MESSAGE_SIZE] = 0;
		trace(cU("Starting process failed"), errorInfo->message, 1);
		return RFC_EXTERNAL_FAILURE;
	}
	else trace(cU("Process started successfully"), NULL, 1);
#else
	FILE* pipe = popenU(command, cU("r"));

	if (pipe == NULL){
        /*CCQ_SECURE_LIB_OK*/
		strncpyU(errorInfo->message, strerrorU(errno), ERROR_MESSAGE_SIZE);
		errorInfo->message[ERROR_MESSAGE_SIZE] = 0;
		trace(cU("Starting process failed"), errorInfo->message, 1);
		return RFC_EXTERNAL_FAILURE;
	}
	else trace(cU("Process started successfully"), NULL, 1);

	RFC_TABLE_HANDLE pipedata;

	rc = RfcGetTable(funcHandle, cU("PIPEDATA"), &pipedata, errorInfo);
	if (rc != RFC_OK){
		trace(cU("Getting PIPEDATA table failed"), errorInfo->message, 1);
		rc = RFC_EXTERNAL_FAILURE;
		goto cleanup;
	}

	while(fgetsU(command, 80, pipe)){
		if (*readPipe != cU('X'))
			continue;

		RfcAppendNewRow(pipedata, errorInfo);
		if (errorInfo->code != RFC_OK){
			rc = RFC_EXTERNAL_FAILURE;
			goto cleanup;
		}

		// remove newline and tabs from the end
		size_t str_len = strlenU(command);
		if (command[str_len-2] == cU('\r') && command[str_len-1] == cU('\n'))
			str_len -= 2;
		else if (command[str_len-1] == cU('\n') || command[str_len-1] == cU('\t') || command[str_len-1] == cU('\r'))
			--str_len;

		// replace tab by a space (may occur in the middle of the line, e.g. with the command "dir" on UNIX)
		SAP_UC* current_pos = strchrU(command, cU('\t'));
		while (current_pos)
		{
			*current_pos = cU(' ');
			current_pos = strchrU(current_pos, cU('\t'));
		}

		RfcSetChars(pipedata, cU("PIPEDATA"), command, str_len, errorInfo);
		if (errorInfo->code != RFC_OK){
			rc = RFC_EXTERNAL_FAILURE;
			goto cleanup;
		}
	}

	cleanup:
	pclose(pipe);
#endif
	return rc;
}

/**
 * \brief  Stops the RFC server, when program is ended.
 * \ingroup rfcexec
 */
#ifdef SAPonNT
BOOL WINAPI shutdownHandler(DWORD dwCtrlType)
{
	theServer->running = false;
	Sleep(2000);
	return FALSE;
}
#else
extern "C" void shutdownHandler(int sig)
{
	theServer->running = false;
}
#endif

/**
 * \brief  Starts the program
 * \ingroup rfcexec
 *
 * Either started from the command line (registered mode) or by the gateway process (started mode).
 * In both cases the program opens a server connection to the backend, installs a handler for the
 * FM RFC_REMOTE_EXEC and waits for incoming requests for that FM.
 * 
 * \in argc Number of arguments provided for startup.
 * \in **argv If started from the command line, the arguments must include the gateway host (-g),
 * the gateway service (-x) and the program ID under which to register (-a). Optionally they may
 * include a filename for reading access restrictions (-f) and a flag to turn on trace (-t).
 * If started from the gateway process, the arguments must consist of the connection parameters
 * required by the CPIC library.
 * \return 0 on success, 1 if anything goes wrong.
 */
int mainU (int argc, SAP_UC** argv){
	RFC_ERROR_INFO errorInfo;
	memsetR(&errorInfo, 0, sizeofR(RFC_ERROR_INFO));

#ifdef SAPonNT
	SetConsoleCtrlHandler(shutdownHandler, TRUE);
#else
	signal(SIGINT, shutdownHandler);
	signal(SIGTERM, shutdownHandler);
	signal(SIGQUIT, shutdownHandler);
#endif

	try{
		RfcExecServer::initMetadata();

		if (RfcInstallServerFunction(NULL, RfcExecServer::rfc_exec, RFC_REMOTE_EXEC, &errorInfo) != RFC_OK){
			throw errorInfo;
		}
		if (RfcInstallServerFunction(NULL, RfcExecServer::rfc_pipe, RFC_REMOTE_EXEC, &errorInfo) != RFC_OK){
			throw errorInfo;
		}

		theServer = new RfcExecServer(argc, argv);
		theServer->trace(cU("RfcExecServer created successfully"), NULL);
		theServer->run();
		theServer->trace(cU("RfcExecServer is shutting down"), NULL);
		delete theServer;
	}
	catch (RFC_ERROR_INFO err){
		RfcExecServer::usage(err.message);
		if (theServer){
			theServer->trace(cU("RfcExecServer aborted with error"), err.message);
			delete theServer;
		}
		return 1;
	}
	catch (SAP_UC* message){
		RfcExecServer::usage(message);
		if (theServer){
			theServer->trace(cU("RfcExecServer aborted with error"), message);
			delete theServer;
		}
		return 1;
	}

	return 0;
}

/**
 * \brief  Constructor for our RFC Server
 * \ingroup rfcexec
 *
 * Parses the command line and then opens a server connection either in started mode or registered mode.
 * Also initializes the access restriction list, if specified.
 * 
 * \in argc See mainU
 * \in **argv See mainU
 */
RfcExecServer::RfcExecServer(int argc, SAP_UC** argv) :
    running(true),
    connection(NULL),
    secureMode(false),
    traceFile(NULL),
    backendRequestedTrace(false)
{
	RFC_ERROR_INFO errorInfo;
        SAP_UC error[256] = iU("");

	memsetU(system, cU('\0'), sizeofU(system));

	std::vector<const SAP_UC*> additionalParams(5);
	additionalParams[0] = cU("-on_cce");
	additionalParams[1] = cU("-cfit");
	additionalParams[2] = cU("-keepalive");
	additionalParams[3] = cU("-delta");
	additionalParams[4] = cU("-no_compression");

	for (int i = 1; i < argc; ++i){
		RFC_CONNECTION_PARAMETER param;

		std::vector<const SAP_UC*>::const_iterator found_it =
			std::find_if(additionalParams.begin(), additionalParams.end(), StrCmp(argv[i]));

		if (found_it == additionalParams.end())
			continue;
		else
			param.name = *found_it + 1; // +1 to get rid of the "-" char

		if (i == argc-1){
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(error, cU("Missing value for parameter %s"), argv[i]);
			goto cleanup;
		}

		param.value = argv[++i];
		connectionParams.push_back(param);
	}

	if (	argc > 4 &&
			(!strncmpU(argv[2],cU("sapgw"),5) || !strncmpU(argv[2],cU("33"),2) || !strncmpU(argv[2],cU("48"),2)) &&
			strlenU(argv[3]) == 8 && 
			isdigitU(argv[3][0]) && 
			isdigitU(argv[3][1]) && 
			isdigitU(argv[3][2]) && 
			isdigitU(argv[3][3]) && 
			isdigitU(argv[3][4]) && 
			isdigitU(argv[3][5]) && 
			isdigitU(argv[3][6]) && 
			isdigitU(argv[3][7])
		){ //Started Server
		registered = false;

		for (int i=2; i<argc; i++){
			if (!strncmpU(argv[i], cU("-t"), 2) ||
			    (!strncmpU(argv[i], cU("CPIC_TRACE="), 11) && argv[i][11] > cU('0'))){
				openTrace();
			}
		}

		parseCommandFile(cU("rfcexec.sec"));
		connection = RfcStartServer(argc, argv, &connectionParams[0], connectionParams.size(), &errorInfo);
		if (connection == NULL) goto cleanup;
	}
	else{ //Registered Server
		unsigned flags = 0;
                RFC_CONNECTION_PARAMETER param;

		registered = true;

		for (int i=1; i<argc; i++){
			if (!strcmpU(cU("-a"), argv[i])){
				if ((flags & 1) == 1){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Duplicate parameter \"-a\""), 25);
					goto cleanup;
				}
				flags |= 1;
				param.name = cU("program_id");
			}
			else if (!strcmpU(cU("-g"), argv[i])){
				if ((flags & 2) == 2){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Duplicate parameter \"-g\""), 25);
					goto cleanup;
				}
				flags |= 2;
				param.name = cU("gwhost");
			}
			else if (!strcmpU(cU("-x"), argv[i])){
				if ((flags & 4) == 4){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Duplicate parameter \"-x\""), 25);
					goto cleanup;
				}
				flags |= 4;
				param.name = cU("gwserv");
			}
			else if (!strcmpU(cU("-t"), argv[i])){
				openTrace();
				continue;
			}
			else if (!strcmpU(cU("-f"), argv[i])){
				if ((flags & 8) == 8){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Duplicate parameter \"-f\""), 25);
					goto cleanup;
				}
				flags |= 8;
				if (i == argc-1){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Missing file name"), 18);
					goto cleanup;
				}
				parseCommandFile(argv[++i]);
				continue;
			}
			else if (!strcmpU(cU("-s"), argv[i])){
				if ((flags & 16) == 16){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Duplicate parameter \"-s\""), 25);
					goto cleanup;
				}
				flags |= 16;
				if (i == argc-1){
					/*CCQ_SECURE_LIB_OK*/
					strncpyU(error, cU("Missing system name"), 20);
					goto cleanup;
				}
				/*CCQ_SECURE_LIB_OK*/
				strncpyU(system, argv[++i], 8);
				continue;
			}
			else if (std::find_if(additionalParams.begin(), additionalParams.end(), StrCmp(argv[i])) == additionalParams.end()){
				/*CCQ_SECURE_LIB_OK*/
				if (traceFile)
					fprintfU(traceFile, cU("Unknown parameter: %s\n"), argv[i]); 
				printfU(cU("Unknown parameter: %s\n"), argv[i]); 
				continue;
			}

			if (i == argc-1){
				/*CCQ_SECURE_LIB_OK*/
				sprintfU(error, cU("Missing value for parameter %s"), argv[i]);
				goto cleanup;
			}

			param.value = argv[++i];
                        connectionParams.push_back(param);
		}

		if ((flags & 7) != 7){
			/*CCQ_SECURE_LIB_OK*/
			strncpyU(error, cU("Not all mandatory parameters specified"), 39); 
			goto cleanup;
		}

		connection = RfcRegisterServer(&connectionParams[0], connectionParams.size(), &errorInfo);
		if (connection == NULL) goto cleanup;
	}

	printTraceHeader();

	return;

	cleanup:
	if (traceFile){
		if (*error == cU('\0')) fprintfU(traceFile, cU("Initializing RfcExecServer failed:\t%s\n"), errorInfo.message);
		else fprintfU(traceFile, cU("Initializing RfcExecServer failed:\t%s\n"), error);
		closeTrace();
	}

	if (*error == cU('\0')) throw errorInfo;
	else throw error;
}

/**
 * \brief  Destructor for our RFC Server
 * \ingroup rfcexec
 *
 * Closes the underlying connection and the trace file and cleans up any occupied memory.
 */
RfcExecServer::~RfcExecServer(void){
	if (connection) RfcCloseConnection(connection, NULL);
	closeTrace();

	vector<SAP_UC*>::iterator it = allowed.begin();
	vector<SAP_UC*>::iterator end = allowed.end();
	while (it != end){
		delete[] *it;
		it++;
	}
	allowed.clear();
}

/**
 * \brief  Prints instructions for how to start this program.
 * \ingroup rfcexec
 *
 * Optionally it prints an error message for more information on why the current start attempt failed.
 * 
 * \in *param An optional error message to print before the instructions. Set to NULL, if not needed.
 */
void RfcExecServer::usage(SAP_UC* param){
	if (param) printfU(cU("Error: %s\n"), param);
	printfU(cU("\tPlease start the program in the following way:\n"));
	printfU(cU("\trfcexec -t -a <program ID> -g <gateway host> -x <gateway service>\n\t\t-f <file with list of allowed commands> -s <allowed Sys ID>\n"));
	printfU(cU("The options \"-t\" (trace), \"-f\" and \"-s\" are optional.\n\n"));
	printfU(cU("Below further optional parameters are listed. You can find their\n"));
	printfU(cU("documentation in sapnwrfc.ini:\n"));
        printfU(cU("-on_cce <0, 1, 2> (On Character Conversion Error)\n"));
        printfU(cU("-cfit (Conversion Fault Indicator Token - the substitute symbol used if on_cce=2)\n"));
        printfU(cU("-keepalive (Sets the keepalive option. Default is 0.)\n"));
        printfU(cU("-delta <0, 1> (default 1, i.e. use delta-manager)\n"));
        printfU(cU("-no_compression (table compression, default is 0, i.e. compression is on)\n"));
}

/**
 * \brief  Main loop of the program.
 * \ingroup rfcexec
 *
 * This function waits for incoming RFC requests from the backend and dispatches them to the
 * RFC_REMOTE_EXEC function. When running in registered mode, the program loops as long as it
 * can still connect to the gateway. When running in started mode, it loops just once.
 */
void RfcExecServer::run(void){
	RFC_RC rc;
	RFC_ERROR_INFO errorInfo;
	bool refresh;

	while(connection != NULL && running){
		refresh = false;

		rc = RfcListenAndDispatch(connection, 2, &errorInfo);
		switch (rc){
			case RFC_NOT_FOUND:
				printfU(cU("Unknown function module: %s\n"), errorInfo.message);
				trace(cU("Unknown function module"), errorInfo.message);
				refresh = true;
				break;
			case RFC_EXTERNAL_FAILURE:
				printfU(cU("SYSTEM_FAILURE has been sent to backend: %s\n"), errorInfo.message);
				trace(cU("SYSTEM_FAILURE has been sent to backend"), errorInfo.message);
				refresh = true;
				break;
			case RFC_ABAP_MESSAGE:
				printfU(cU("ABAP Message has been sent to backend: %s %s %s\n"), errorInfo.abapMsgType,
							errorInfo.abapMsgClass, errorInfo.abapMsgNumber);
				printfU(cU("Variables: V1=%s V2=%s V3=%s V4=%s\n"), errorInfo.abapMsgV1,
							errorInfo.abapMsgV2, errorInfo.abapMsgV3, errorInfo.abapMsgV4);
				refresh = true;
				break;
			case RFC_CLOSED:
			case RFC_INVALID_HANDLE:
			case RFC_MEMORY_INSUFFICIENT:
			case RFC_COMMUNICATION_FAILURE:
				printfU(cU("Communication Failure: %s\n"), errorInfo.message);
				trace(cU("Communication Failure"), errorInfo.message);
				refresh = true;
				connection = NULL;
				break;
            default:
                break;
		}

		if (refresh && registered){
			trace(cU("Trying to reconnect..."), NULL);
			connection = RfcRegisterServer(&connectionParams[0], connectionParams.size(), &errorInfo);
			if (connection == NULL){
				printfU(cU("Error: unable to reconnect to %s. %s:%s\n"), system,
						RfcGetRcAsString(errorInfo.code), errorInfo.message);
				printfU(cU("Stopping to listen at %s\n"), system);
				trace(cU("Error: unable to reconnect"), errorInfo.message);
				trace(cU("Stopping to listen at"), system);
			}
			else trace(cU("...success"), NULL);
		}
	}
}

/**
 * \brief  Creates a hard-coded metadata description of the FM RFC_REMOTE_EXEC as used by
 * the ALE interface.
 * \ingroup rfcexec
 * 
 * Note that the table PIPEDATA has been implemented by the original rfcexec program, but is
 * not used in the ALE standard functionality. Other EDI subsystems may use it though, therefore
 * it remains part of the interface.
 */
void RfcExecServer::initMetadata(void){
	RFC_ERROR_INFO errorInfo;
	RFC_RC rc = RFC_OK;
	RFC_PARAMETER_DESC paramDescr;
	RFC_TYPE_DESC_HANDLE tableStruct;
	RFC_FIELD_DESC fieldDescr;

	memsetU(paramDescr.defaultValue, cU('\0'), sizeofU(RFC_PARAMETER_DEFVALUE));
	paramDescr.extendedDescription = 0;
	paramDescr.optional = 0;
	memsetU(paramDescr.parameterText, cU('\0'), sizeofU(RFC_PARAMETER_TEXT));

	rfc_exec = RfcCreateFunctionDesc(cU("RFC_REMOTE_EXEC"), &errorInfo);
	if (rfc_exec == NULL) throw errorInfo;
	rfc_pipe = RfcCreateFunctionDesc(cU("RFC_REMOTE_PIPE"), &errorInfo);
	if (rfc_pipe == NULL) throw errorInfo;

	/*CCQ_SECURE_LIB_OK*/
	strncpyU(paramDescr.name, cU("COMMAND"), 8);
	paramDescr.type = RFCTYPE_CHAR;
	paramDescr.direction = RFC_IMPORT;
	paramDescr.nucLength = 256;
	paramDescr.ucLength = 512;
	paramDescr.decimals = 0;
	paramDescr.typeDescHandle = NULL;
	rc = RfcAddParameter(rfc_exec, &paramDescr, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;
	rc = RfcAddParameter(rfc_pipe, &paramDescr, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;

	/*CCQ_SECURE_LIB_OK*/
	strncpyU(paramDescr.name, cU("READ"), 5);
	paramDescr.type = RFCTYPE_CHAR;
	paramDescr.direction = RFC_IMPORT;
	paramDescr.nucLength = 1;
	paramDescr.ucLength = 2;
	paramDescr.decimals = 0;
	paramDescr.typeDescHandle = NULL;
	rc = RfcAddParameter(rfc_pipe, &paramDescr, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;

	tableStruct = RfcCreateTypeDesc(cU("PIPEDATA"), &errorInfo);
	if (tableStruct == NULL) throw errorInfo;

	/*CCQ_SECURE_LIB_OK*/
	strncpyU(fieldDescr.name, cU("PIPEDATA"), 9);
	fieldDescr.type = RFCTYPE_CHAR;
	fieldDescr.nucLength = 80;
	fieldDescr.nucOffset = 0;
	fieldDescr.ucLength = 160;
	fieldDescr.ucOffset = 0;
	fieldDescr.decimals = 0;
	fieldDescr.typeDescHandle = NULL;
	fieldDescr.extendedDescription = NULL;
	rc = RfcAddTypeField(tableStruct, &fieldDescr, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;

	rc = RfcSetTypeLength(tableStruct,80, 160, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;

	/*CCQ_SECURE_LIB_OK*/
	strncpyU(paramDescr.name, cU("PIPEDATA"), 9);
	paramDescr.type = RFCTYPE_TABLE;
	paramDescr.direction = RFC_TABLES;
	paramDescr.nucLength = 8;
	paramDescr.ucLength = 8;
	paramDescr.decimals = 0;
	paramDescr.typeDescHandle = tableStruct;
	rc = RfcAddParameter(rfc_exec, &paramDescr, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;
	rc = RfcAddParameter(rfc_pipe, &paramDescr, &errorInfo);
	if (rc != RFC_OK) throw errorInfo;
}

/**
 * \brief  Opens the trace file.
 * \ingroup rfcexec
 *
 * We don't throw an error, if opening the trace file fails, because tracing should
 * not disrupt the productive functionality of the program.
 */
void RfcExecServer::openTrace(void){
    time_t     currTime = time( NULL );
    if (traceFile == NULL)
    {
	    SAP_UC tracefile_name[128] = iU("");
	    sprintfU (tracefile_name, /*CCQ_FORMAT_STRING_OK*/cU("rfcexec%.5d_%05llu.trc"), getpid(), (long long)currTime); 
        traceFile = fopenU(tracefile_name, cU("wt"));
    }
	if (traceFile){
		SAP_UC cwd[512];
		/*CCQ_CLIB_LOCTIME_OK*/ 
		fprintfU(traceFile, cU("***** Rfcexec trace file opened at %s\n"), ctimeU(&currTime));
		trace(cU("NW RFC SDK Version"), RfcGetVersion(NULL, NULL, NULL));
		getcwdU(cwd,sizeofU(cwd));
		fprintfU(traceFile, cU("***** Current working directory: %s\n"), cwd);
	}
}

/**
 * \brief  Closes the trace file.
 * \ingroup rfcexec
 */
void RfcExecServer::closeTrace(void){
	if (traceFile){
        time_t     currTime = time( NULL );
		/*CCQ_CLIB_LOCTIME_OK*/ 
		fprintfU(traceFile, cU("***** Rfcexec trace file closed at %s\n"), ctimeU(&currTime));
		fclose(traceFile);
		traceFile = NULL;
	}
}

/**
 * \brief  Prints the used security settings to the trace file.
 * \ingroup rfcexec
 */
void RfcExecServer::printTraceHeader(void){
	if (secureMode){
		if(traceFile){
			trace(cU("Using secure mode. Allowing connections only for the following USER:SYSID:CLIENT:PROGRAM combinations"), NULL);
			vector<SAP_UC*>::iterator it = allowed.begin();
			vector<SAP_UC*>::iterator end = allowed.end();
			while (it != end){
				trace(*it, NULL, 1);
				it++;
			}
		}
	}
	else{
		trace(cU("Using default mode. Allowing connections only from Report SAPLEDI7 and System"), system);
	}
	trace(cU("\t----------\n"), NULL);
}

/**
 * \brief  Writes an entry to the trace file.
 * \ingroup rfcexec
 *
 * We don't throw an error, if writing the trace entry fails, because tracing should
 * not disrupt the productive functionality of the program.
 *
 * \in key The "variable name" of the variable to trace, or a "heading".
 * \in value The value of the variable to trace, or a "message".
 * \in indent Start the line with n tabs. Optional. Default is 0.
 */
void RfcExecServer::trace(const SAP_UC* key, const SAP_UC* value, int indent){
	if (traceFile){
		while (indent--) fprintfU(traceFile, cU("\t"));
		if (value) fprintfU(traceFile, cU("%s:\t%s\n"), key, value);
		else fprintfU(traceFile, cU("%s\n"), key);
		fflush(traceFile);
	}
}

/**
 * \brief  Parses the file containing detailed access restrictions for this program.
 * \ingroup rfcexec
 * 
 * This program can be started with an additional file containing detailed information about
 * which SAP user from which R/3 system and which client may execute which OS command.
 * Each line of the file must be in the following format:
 *
 * USER=EDIUSER,SYSID=XYZ,CLIENT=000,PATH=/usr/bin/edi_sub_system.sh
 *
 * \in *filePath Path and filename specifying the file to read.
 */
void RfcExecServer::parseCommandFile(const SAP_UC* filePath)
{
	FILE* commandFile = NULL;
	SAP_UC buf[1025] = iU(""), *temp = NULL, *user = NULL, *sysid = NULL, *client = NULL, *path = NULL;
	size_t lineLength = 0;
	unsigned line = 0;
	
	commandFile = fopenU(filePath, cU("rt"));

	if (commandFile == NULL){
		if (errno == ENOENT && !registered) return; // No file is ok, we use the default mode (ALE scenario).

		trace(cU("Error in parseCommandFile"), strerrorU(errno));
		closeTrace();
		throw strerrorU(errno);
	}

	trace(cU("Reading command file"), filePath, 1);

	while(fgetsU(buf, sizeofU(buf), commandFile)){
		line++;
		trace(buf, NULL, 1);
		/*CCQ_SECURE_LIB_OK*/
		lineLength = strlenU(buf);
		if (lineLength == 1024 && buf[1023] != cU('\n')){
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(buf, cU("Line no. %d is too long. Limit: 1024"), line);
			goto error;
		}
		else if (lineLength < 30){
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(buf,  cU("Line no. %d is invalid."), line);
			goto error;
		}

		if (buf[lineLength-1] == cU('\n')) buf[--lineLength] = cU('\0');

		user = sysid = client = path = NULL;
		temp = strtokU(buf, cU(","));
		while (temp){
			if (strncmpU(temp, cU("USER="), 5) == 0) user = temp+5;
			else if (strncmpU(temp, cU("SYSID="), 6) == 0) sysid = temp+6;
			else if (strncmpU(temp, cU("CLIENT="), 7) == 0) client = temp+7;
			else if (strncmpU(temp, cU("PATH="), 5) == 0) path = temp+5;
			else{
				/*CCQ_SECURE_LIB_OK*/
				sprintfU(buf,  cU("Line no. %d contains invalid parameter."), line);
				goto error;
			}
			temp = strtokU(NULL, cU(","));
		}

		if (user == NULL || sysid == NULL || client == NULL || path == NULL){
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(buf,  cU("Missing parameter in line no. %d"), line);
			goto error;
		}
		if (strlenU(sysid) > 8){
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(buf,  cU("Invalid SYSID in line no. %d"), line);
			goto error;
		}
		if (strlenU(client) != 3){
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(buf,  cU("Invalid CLIENT in line no. %d"), line);
			goto error;
		}

		lineLength = 12 + strlenU(user) + strlenU(sysid) + strlenU(path);
		temp = new SAP_UC[lineLength];
		/*CCQ_SECURE_LIB_OK*/
		sprintfU(temp, cU("U:%sS:%sC:%sP:%s"), user, sysid, client, path);

		allowed.push_back(temp);
	}

	secureMode = true;
	fclose(commandFile);
	trace(cU("End of file"), NULL, 1);
	return;

	error: fclose(commandFile);
	trace(cU("Error"), buf);
	throw buf;
}

/**
 * \brief  Checks whether the current SAP user is allowed to execute the given OS command.
 * \ingroup rfcexec
 * 
 * If the program has been started with the extra parameter -f \<filename>, the given user,
 * SAP system ID, client and OS command and matched against the cached entries of the file.
 * Access is allowed, only if an exact match can be found.
 *
 * Otherwise the program verifies only, that the call came from the correct SAP system and
 * that the calling program is the ALE layer (SAPLEDI7).
 * 
 * \in user The current backend user calling the server program
 * \in sysid System ID of the calling backend
 * \in client The Client ("Mandant", not the opposite of "Server"...!) from which the call came
 * \in path The program to be started, given by relative or absolute path. Came from the 
 * function module import parameter COMMAND
 * \in caller Name of the ABAP Report/Function Group, which issued the CALL FUNCTION statement.
 * Used only in "default mode".
 * \return true means: this call is allowed, false means: it's denied.
 */
bool RfcExecServer::checkAuthorization(SAP_UC* user, SAP_UC* sysid, SAP_UC* client, SAP_UC* path, SAP_UC* caller){
	if (traceFile){
		trace(cU("User"), user, 1);
		trace(cU("SysID"), sysid, 1);
		trace(cU("Client"), client, 1);
		trace(cU("Program"), path, 1);
		trace(cU("Calling Report"), caller, 1);
	}
	if (secureMode){
		size_t len = 9 + strlenU(user) + strlenU(sysid) + strlenU(client) + strlenU(path);
		// I'll leave strlenU(client) in here, because this function may be called with an
		// invalid (longer) client input...

		SAP_UC* temp = new SAP_UC[len];
		/*CCQ_SECURE_LIB_OK*/
		sprintfU(temp, cU("U:%sS:%sC:%sP:%s"), user, sysid, client, path);
		vector<SAP_UC*>::iterator it = allowed.begin();
		vector<SAP_UC*>::iterator end = allowed.end();
		while (it != end && strncmpU(temp, *it, len) != 0) it++;

		if (it == end){
			SAP_UC* allowedPath;
			size_t allowedPathLen;
			it = allowed.begin();
			/*CCQ_SECURE_LIB_OK*/
			sprintfU(temp, cU("U:%sS:%sC:%sP:"), user, sysid, client);
			len -= (strlenU(path)+1);
			while (it != end){
				if (strncmpU(temp, *it, len) == 0){
					allowedPath = (*it) + len;
					allowedPathLen = strlenU(allowedPath);
					if (allowedPath[allowedPathLen-1] == cU('*') && strncmpU(allowedPath, path, allowedPathLen-1) == 0){
						delete[] temp;
						return true;
					}
				}
				it++;
			}
			delete[] temp;
			return false;
		}
		else{
			delete[] temp;
			return true;
		}
	}
	else{
		if (strcmpU(caller, cU("SAPLEDI7")) == 0 && (*system == cU('\0') || strcmpU(sysid, system) == 0)) return true;
		else return false;
	}
}
