#include <stdlib.h>
#include <stdio.h>
#include "sapnwrfc.h"

void errorHandling(RFC_RC rc, SAP_UC* description, RFC_ERROR_INFO* errorInfo, RFC_CONNECTION_HANDLE connection){
	printfU(cU("%s: %d\n"), description, rc);
	printfU(cU("%s: %s\n"), errorInfo->key, errorInfo->message);
	// It's better to close the TCP/IP connection cleanly, than to just let the
	// backend get a "Connection reset by peer" error...
	if (connection != NULL) RfcCloseConnection(connection, errorInfo);

	exit(1);
}

RFC_RC SAP_API serverFunction(RFC_CONNECTION_HANDLE rfcHandle, RFC_FUNCTION_HANDLE funcHandle, RFC_ERROR_INFO* pErrorInfo){
	RFC_RC rc = RFC_OK;
	RFC_CONNECTION_HANDLE connection = NULL;
	unsigned length = 2048;
	SAP_UC* ticket = (SAP_UC*)mallocU(length);
	RFC_CONNECTION_PARAMETER loginParams[5];
	RFC_ATTRIBUTES attributes;

	// Notifying the user that we got something
	rc = RfcGetConnectionAttributes(rfcHandle, &attributes, pErrorInfo);
	if (RFC_OK == rc) printfU(cU("\tGot a call from %s\n"), attributes.sysId);

	// Reading the SSO ticket. We don't need to check, whether malloc() gave us any memory:
	// RfcGetPartnerSSOTicket() does it for us.
	rc = RfcGetPartnerSSOTicket(rfcHandle, ticket, &length, pErrorInfo);
	if (rc == RFC_BUFFER_TOO_SMALL){
		ticket = (SAP_UC*)reallocU(ticket, length);
		rc = RfcGetPartnerSSOTicket(rfcHandle, ticket, &length, pErrorInfo);
	}

	if (rc == RFC_OK && length == 0){ // This is an error...: the backend didn't send a ticket.
		// RfcGetPartnerSSOTicket() sets length to 0 and returns RFC_OK in that case.
		pErrorInfo->code = RFC_EXTERNAL_FAILURE;
		pErrorInfo->group = EXTERNAL_APPLICATION_FAILURE;
		strcpyU(pErrorInfo->message, cU("Didn't get a ticket from backend!"));
		printfU(cU("\tError: %s\n"), pErrorInfo->message);
		free(ticket); // malloc() or realloc() above must have been successful, otherwise we
		// would have gotten rc = RFC_INVALID_PARAMETER at this point.
		return pErrorInfo->code;
	}
	else if (rc != RFC_OK){
		if (ticket) free(ticket); // We could be here, because ticket = NULL and consequently rc = RFC_INVALID_PARAMETER.
		return rc; // pErrorInfo->message should already be filled with a meaningful error message.
	}

	/* Now we log on using that ticket. Here we could also log into a different system
	that accepts the ticket, but in order to make this code run in any environment, we
	log back into the system from where we got the call. */
	printfU(cU("\tGot a ticket. Trying to use it for logging into the backend...\n"));
	loginParams[0].name = cU("ashost");		loginParams[0].value = attributes.partnerHost;
	loginParams[1].name = cU("sysnr");		loginParams[1].value = attributes.sysNumber;
	loginParams[2].name = cU("client");		loginParams[2].value = attributes.client;
	loginParams[3].name = cU("lang");		loginParams[3].value = attributes.language;
	loginParams[4].name = cU("mysapsso2");	loginParams[4].value = ticket;
	connection = RfcOpenConnection(loginParams, 5, pErrorInfo);
	if (connection == NULL){
		pErrorInfo->code = RFC_EXTERNAL_FAILURE;
		pErrorInfo->group = EXTERNAL_APPLICATION_FAILURE;
		printfU(cU("\tError logging in: %s\n"), pErrorInfo->message);
		free(ticket);
		return pErrorInfo->code;
	}

	printfU(cU("\t...successfully logged on.\n"));
	free(ticket);
	RfcCloseConnection(connection, NULL);

	// Finally send back a little message.
	RfcSetString(funcHandle, cU("ECHOTEXT"), cU("Ha, didn't expect this, did ya?"), 31, NULL);
	return RFC_OK;
}

RFC_FUNCTION_DESC_HANDLE createDescription(){
	RFC_FUNCTION_DESC_HANDLE handle;
	RFC_PARAMETER_DESC REQUTEXT = { iU("REQUTEXT"), RFCTYPE_CHAR, RFC_IMPORT,   255,   510,   0, 0, 0, 0, 0};
	RFC_PARAMETER_DESC ECHOTEXT = { iU("ECHOTEXT"), RFCTYPE_CHAR, RFC_EXPORT,   255,   510,   0, 0, 0, 0, 0};
	RFC_PARAMETER_DESC RESPTEXT = { iU("RESPTEXT"), RFCTYPE_CHAR, RFC_EXPORT,   255,   510,   0, 0, 0, 0, 0};

	handle = RfcCreateFunctionDesc(cU("STFC_CONNECTION"), 0);
	RfcAddParameter(handle, &REQUTEXT, 0);
	RfcAddParameter(handle, &ECHOTEXT, 0);
	RfcAddParameter(handle, &RESPTEXT, 0);
	return handle;
}

int mainU(int argc, SAP_UC** argv){
	RFC_RC rc = RFC_OK;
	RFC_FUNCTION_DESC_HANDLE stfcConnection = NULL;
	RFC_CONNECTION_PARAMETER serverParams[3];
	RFC_ERROR_INFO errorInfo;
	RFC_CONNECTION_HANDLE serverHandle = NULL;
	SAP_UC gwService[8] = iU("sapgw00");

	if (argc < 4){
		printfU(cU("Usage: sso2sample <hostname> <system number> <program ID>\n"));
		return 1;
	}

	if (strlenU(argv[2]) == 2) strncpyU(&gwService[5], argv[2], 2);
	else{
		printfU(cU("<system number> needs to be in the range 00 - 99.\n"));
		return 1;
	}

	serverParams[0].name = cU("gwhost");		serverParams[0].value = argv[1];
	serverParams[1].name = cU("gwserv");		serverParams[1].value = gwService;
	serverParams[2].name = cU("program_id");	serverParams[2].value = argv[3];

	stfcConnection = createDescription();
	rc = RfcInstallServerFunction(NULL, stfcConnection, serverFunction, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error installing server function"), &errorInfo, NULL);

	printfU(cU("Registering Server...\n"));
	serverHandle = RfcRegisterServer(serverParams, 3, &errorInfo);
	if (serverHandle == NULL) errorHandling(rc, cU("Error starting RFC server"), &errorInfo, serverHandle);
	printfU(cU("...done\n"));

	/* Currently the only way to obtain an SSO2 (or assertion) ticket is, if the
	SAP backend gives you one... Therefore this program works as follows:
	1. The program starts an RFC server on the given RFC destination. Make sure that in
	   SM59 in the "Security/Logon" tab you activate the check box "Send SAP Logon Ticket".
	2. The program starts to listen for a call from the backend. Go to SE37, enter the
	   function module STFC_CONNECTION, enter the correct RFC destination and execute the
	   function module.
	3. In the implementing server function for STFC_CONNECTION, the program reads the SSO2
	   or assertion ticket from the backend system and uses it to log into that system.
	If everything works correctly, you get a success message.
	This program handles only one single function call and then exits.*/

	printfU(cU("Starting to listen for one call...\n"));
	rc = RfcListenAndDispatch(serverHandle, -1, &errorInfo);
	if (rc == RFC_OK || rc == RFC_ABAP_EXCEPTION || rc == RFC_RETRY) RfcCloseConnection(serverHandle, NULL);
	// In all other cases the serverHandle is already closed.

	if (rc != RFC_OK) errorHandling(rc, cU("Error processing function call"), &errorInfo, NULL);
	printfU(cU("...done\n"));

	return 0;
}