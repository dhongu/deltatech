#include <stdlib.h>
#include <stdio.h>
#include "sapnwrfc.h"

static int listening = 1;

#if defined(SAPonOS400) || defined(SAPwithPASE400)
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

/*
Unfortunately SE37 does not yet allow to set complex inputs, so in order to test
this example, you will probably need to write a little ABAP report, which sets a few
input lines for IMPORT_TAB and then does a

CALL FUNCTION 'STFC_DEEP_TABLE' DESTINATION 'MY_SERVER'
  EXPORTING
    import_tab       = imtab
  IMPORTING
    export_tab       = extab
    resptext         = text
  EXCEPTIONS
    system_failure          = 1  MESSAGE mes.
    communication_failure   = 2  MESSAGE mes.

This also allows to catch the detail texts for SYSTEM_FAILURES.
Note: STFC_DEEP_TABLE exists only from SAP_BASIS release 6.20 on.
*/

void errorHandling(RFC_RC rc, SAP_UC* description, RFC_ERROR_INFO* errorInfo, RFC_CONNECTION_HANDLE connection){
	printfU(cU("%s: %d\n"), description, rc);
	printfU(cU("%s: %s\n"), errorInfo->key, errorInfo->message);
	// It's better to close the TCP/IP connection cleanly, than to just let the
	// backend get a "Connection reset by peer" error...
	if (connection != NULL) RfcCloseConnection(connection, errorInfo);

	exit(1);
}

RFC_RC SAP_API stfcDeepTableImplementation(RFC_CONNECTION_HANDLE rfcHandle, RFC_FUNCTION_HANDLE funcHandle, RFC_ERROR_INFO* errorInfoP){
	RFC_ATTRIBUTES attributes;
	RFC_TABLE_HANDLE importTab = 0;
	RFC_STRUCTURE_HANDLE tabLine = 0;
	RFC_TABLE_HANDLE exportTab = 0;
	RFC_ERROR_INFO errorInfo ;
	RFC_CHAR buffer[257]; //One for the terminating zero
	RFC_INT intValue;
	RFC_RC rc;
	unsigned tabLen = 0, strLen;
	unsigned  i = 0;
	buffer[256] = 0;

	printfU(cU("\n*** Got request for STFC_DEEP_TABLE from the following system: ***\n"));

	RfcGetConnectionAttributes(rfcHandle, &attributes, &errorInfo);
	printfU(cU("System ID: %s\n"), attributes.sysId);
	printfU(cU("System No: %s\n"), attributes.sysNumber);
	printfU(cU("Mandant  : %s\n"), attributes.client);
	printfU(cU("Host     : %s\n"), attributes.partnerHost);
	printfU(cU("User     : %s\n"), attributes.user);

	//Print the Importing Parameter
	printfU(cU("\nImporting Parameter:\n"));
	RfcGetTable(funcHandle, cU("IMPORT_TAB"), &importTab, &errorInfo);

	RfcGetRowCount(importTab, &tabLen, &errorInfo);
	printfU(cU("IMPORT_TAB (%u lines)\n"), tabLen);
	for (i=0; i<tabLen; i++){
		RfcMoveTo(importTab, i, &errorInfo);
		printfU(cU("\t\t-line %u\n"), i);

		RfcGetInt(importTab, cU("I"), &intValue, &errorInfo);
		printfU(cU("\t\t\t-I:\t%d\n"), intValue);
		RfcGetString(importTab, cU("C"), buffer, 11, &strLen, &errorInfo);
		printfU(cU("\t\t\t-C:\t%s\n"), buffer);
		// Check for the stop flag:
		if (i==0 && strncmpU(cU("STOP"), buffer, 4) == 0) listening = 0;
		RfcGetStringLength(importTab, cU("STR"), &strLen, &errorInfo);
		if (strLen > 256) printfU(cU("UTF8_STRING length bigger than 256: %u. Omitting the STR field...\n"), strLen);
		else{
			RfcGetString(importTab, cU("STR"), buffer, 257, &strLen, &errorInfo);
			printfU(cU("\t\t\t-STR:\t%s\n"), buffer);
		}
		RfcGetStringLength(importTab, cU("XSTR"), &strLen, &errorInfo);
		if (strLen > 128) printfU(cU("XSTRING length bigger than 128: %u. Omitting the XSTR field...\n"), strLen);
		else{
			RfcGetString(importTab, cU("XSTR"), buffer, 257, &strLen, &errorInfo);
			printfU(cU("\t\t\t-XSTR:\t%s\n"), buffer);
		}
	}

	//Now set the Exporting Parameters
	printfU(cU("\nSetting values for Exporting Parameters:\n"));
	printfU(cU("Please enter a value for RESPTEXT:\n> "));
    /*CCQ_SECURE_LIB_OK*/
	getsU(buffer);
    /*CCQ_SECURE_LIB_OK*/
	RfcSetChars(funcHandle, cU("RESPTEXT"), buffer, strlenU(buffer), &errorInfo);
	printfU(cU("\nPlease enter the number of lines in EXPORT_TAB:\n> ")); 
    /*CCQ_SECURE_LIB_OK*/
	getsU(buffer);
	tabLen = atoiU(buffer);
	RfcGetTable(funcHandle, cU("EXPORT_TAB"), &exportTab, &errorInfo);
	for (i=0; i<tabLen; i++){
		tabLine = RfcAppendNewRow(exportTab, &errorInfo);
		printfU(cU("Line %u\n"), i);
		printfU(cU("\tPlease enter a value for C [CHAR10]:> "));
        /*CCQ_SECURE_LIB_OK*/
		getsU(buffer);
        /*CCQ_SECURE_LIB_OK*/
		RfcSetChars(tabLine, cU("C"), buffer, strlenU(buffer), &errorInfo);
		printfU(cU("\tPlease enter a value for I [INT4]:> "));
        /*CCQ_SECURE_LIB_OK*/
		getsU(buffer);
		RfcSetInt(tabLine, cU("I"), atoiU(buffer), &errorInfo);
		printfU(cU("\tPlease enter a value for STR [UTF8_STRING]:> "));
        /*CCQ_SECURE_LIB_OK*/
		fgetsU(buffer, 257, stdin); // For these fields better make sure, the user doesn't bust our buffer...
        /*CCQ_SECURE_LIB_OK*/
		strLen = strlenU(buffer) - 1;
		// In contrast to gets, fgets includes the linebreak... Very consistent...
		RfcSetString(tabLine, cU("STR"), buffer, strLen, &errorInfo);
		mark: printfU(cU("\tPlease enter a value for XSTR [XSTRING]:> "));
        /*CCQ_SECURE_LIB_OK*/
		fgetsU(buffer, 257, stdin);
        /*CCQ_SECURE_LIB_OK*/
		strLen = strlenU(buffer) - 1;
		// In contrast to gets, fgets includes the linebreak... Very consistent...
		rc = RfcSetString(tabLine, cU("XSTR"), buffer, strLen, &errorInfo);
		if (rc != RFC_OK){
			printfU(cU("\tInvalid value for XSTR. Please only use hex digits 00 - FF.\n"));
			goto mark;
		}
	}
	printfU(cU("**** Processing of STFC_DEEP_TABLE finished ***\n\n"));

	return RFC_OK;
}

int mainU(int argc, SAP_UC** argv){
	RFC_RC rc;
	RFC_FUNCTION_DESC_HANDLE stfcDeepTableDesc;
	RFC_CONNECTION_PARAMETER repoCon[8], serverCon[3];
	RFC_CONNECTION_HANDLE repoHandle, serverHandle;
	RFC_ERROR_INFO errorInfo;

	serverCon[0].name = cU("program_id");	serverCon[0].value = cU("MY_SERVER");
	serverCon[1].name = cU("gwhost");		serverCon[1].value = cU("hostname");
	serverCon[2].name = cU("gwserv");		serverCon[2].value = cU("sapgw53");

	repoCon[0].name = cU("client");	repoCon[0].value = cU("000");
	repoCon[1].name = cU("user");		repoCon[1].value = cU("user");
	repoCon[2].name = cU("passwd");	repoCon[2].value = cU("****");
	repoCon[3].name = cU("lang");		repoCon[3].value = cU("DE");
	repoCon[4].name = cU("ashost");	repoCon[4].value = cU("hostname");
	repoCon[5].name = cU("sysnr");	repoCon[5].value = cU("53");

	printfU(cU("Logging in..."));
	repoHandle = RfcOpenConnection (repoCon, 6, &errorInfo);
	if (repoHandle == NULL) errorHandling(errorInfo.code, cU("Error in RfcOpenConnection()"), &errorInfo, NULL);
	printfU(cU(" ...done\n"));

	printfU(cU("Fetching metadata..."));
	stfcDeepTableDesc = RfcGetFunctionDesc(repoHandle, cU("STFC_DEEP_TABLE"), &errorInfo);
	// Note: STFC_DEEP_TABLE exists only from SAP_BASIS release 6.20 on
	if (stfcDeepTableDesc == NULL) errorHandling(errorInfo.code, cU("Error in Repository Lookup"), &errorInfo, repoHandle);
	printfU(cU(" ...done\n"));

	printfU(cU("Logging out..."));
	RfcCloseConnection(repoHandle, &errorInfo);
	printfU(cU(" ...done\n"));

	rc = RfcInstallServerFunction(NULL, stfcDeepTableDesc, stfcDeepTableImplementation, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error Setting "), &errorInfo, repoHandle);

	printfU(cU("Registering Server..."));
	serverHandle = RfcRegisterServer(serverCon, 3, &errorInfo);
	if (serverHandle == NULL) errorHandling(errorInfo.code, cU("Error Starting RFC Server"), &errorInfo, NULL);
	printfU(cU(" ...done\n"));

	printfU(cU("Starting to listen...\n\n"));
	while(RFC_OK == rc || RFC_RETRY == rc || RFC_ABAP_EXCEPTION == rc){
		rc = RfcListenAndDispatch(serverHandle, 120, &errorInfo);
		printfU(cU("RfcListenAndDispatch() returned %s\n"), RfcGetRcAsString(rc));
		switch (rc){
			case RFC_OK:
				break;
			case RFC_RETRY:	// This only notifies us, that no request came in within the timeout period.
						    // We just continue our loop.
				printfU(cU("No request within 120s.\n"));
				break;
			case RFC_ABAP_EXCEPTION:	// Our function module implementation has returned RFC_ABAP_EXCEPTION.
								// This is equivalent to an ABAP function module throwing an ABAP Exception.
								// The Exception has been returned to R/3 and our connection is still open.
								// So we just loop around.
				printfU(cU("ABAP_EXCEPTION in implementing function: %s\n"), errorInfo.key);
				break;
			case RFC_NOT_FOUND:	// R/3 tried to invoke a function module, for which we did not supply
							    // an implementation. R/3 has been notified of this through a SYSTEM_FAILURE,
							    // so we need to refresh our connection.
				printfU(cU("Unknown function module: %s\n"), errorInfo.message);
            /*FALLTHROUGH*/
            case RFC_EXTERNAL_FAILURE:	// Our function module implementation raised a SYSTEM_FAILURE. In this case
								        // the connection needs to be refreshed as well.
				printfU(cU("SYSTEM_FAILURE has been sent to backend.\n\n"));
            /*FALLTHROUGH*/
			case RFC_COMMUNICATION_FAILURE:
			case RFC_ABAP_MESSAGE:		// And in these cases a fresh connection is needed as well
            default:
                serverHandle = RfcRegisterServer(serverCon, 3, &errorInfo);
				rc = errorInfo.code;
				break;
		}

		// This allows us to shutdown the RFC Server from R/3. The implementation of STFC_DEEP_TABLE
		// will set listening to false, if IMPORT_TAB-C == STOP.
		if (!listening){
			RfcCloseConnection(serverHandle, NULL);
			break;
		}
	}

	return 0;
}
