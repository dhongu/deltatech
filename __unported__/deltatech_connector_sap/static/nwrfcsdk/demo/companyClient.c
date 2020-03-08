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

//usage: companyClient <hostname> <system Number> <client> <user> <language> <password>
int mainU(int argc, SAP_UC** argv){
	RFC_RC rc = RFC_OK;
	RFC_CONNECTION_PARAMETER loginParams[6];
	RFC_ERROR_INFO errorInfo;
	RFC_CONNECTION_HANDLE connection;
	RFC_FUNCTION_DESC_HANDLE bapiCompanyDesc;
	RFC_FUNCTION_HANDLE bapiCompany;
	RFC_STRUCTURE_HANDLE returnStructure;
	SAP_UC message[221] = iU("");
	RFC_BYTE buffer[1105];
	unsigned utf8Len = 1105, resultLen;
	FILE* outFile;

	loginParams[0].name = cU("ashost");	loginParams[0].value = argc > 1 ? argv[1] : cU("hostname");
	loginParams[1].name = cU("sysnr");	loginParams[1].value = argc > 2 ? argv[2] : cU("05");
	loginParams[2].name = cU("client");	loginParams[2].value = argc > 3 ? argv[3] : cU("800");
	loginParams[3].name = cU("user");	loginParams[3].value = argc > 4 ? argv[4] : cU("user");
	loginParams[4].name = cU("passwd");	loginParams[4].value = argc > 5 ? argv[5] : cU("*****");
	loginParams[5].name = cU("lang");	loginParams[5].value = argc > 6 ? argv[6] : cU("JA");

	connection = RfcOpenConnection(loginParams, 6, &errorInfo);
	if (connection == NULL) errorHandling(rc, cU("Error during logon"), &errorInfo, NULL);

	bapiCompanyDesc = RfcGetFunctionDesc(connection, cU("BAPI_COMPANY_GETDETAIL"), &errorInfo);
	if (bapiCompanyDesc == NULL) errorHandling(rc, cU("Error during metadata lookup"), &errorInfo, connection);

	bapiCompany = RfcCreateFunction(bapiCompanyDesc, &errorInfo);

	// Use a company ID that does not exit. 000007 should not exist in most systems.
	RfcSetChars(bapiCompany, cU("COMPANYID"), cU("000007"), 6, &errorInfo);

	rc = RfcInvoke(connection, bapiCompany, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error calling BAPI_COMPANY_GETDETAIL"), &errorInfo, connection);

	RfcGetStructure(bapiCompany, cU("RETURN"), &returnStructure, &errorInfo);
	RfcGetString(returnStructure, cU("MESSAGE"), message, 221, &resultLen, &errorInfo);
	RfcDestroyFunction(bapiCompany, &errorInfo);
	RfcCloseConnection(connection, NULL);

	// On Windows you can use the following function from windows.h toconvert to UTF-8:
	// utf8Len = WideCharToMultiByte(CP_UTF8, 0, message, strlenU(message), buffer, 1105, NULL, NULL);
	// It will have a slightly better performance than RfcSAPUCToUTF8().
	
	// On 'system i' with Japanese double byte characters using the ASCII LIBSAPNRFC the
	// message string does not contain UNICODE but JIS encoded data. The call to the
	// following function does not make any sense in this case. Instead you can add an
	// encoding to the header lilke this: "<?xml version=\"1.0\" encoding=\"Shift-JIS\"?>\n<message>",
	// and fputs the message directly some lines below:
	// fwrite(buffer, 1, utf8Len, outFile); ==> fputs((char*)message, outFile);
	/*CCQ_SECURE_LIB_OK*/
    RfcSAPUCToUTF8(message,  strlenU(message), buffer, &utf8Len,  &resultLen, &errorInfo);

	outFile = fopenU(cU("message.xml"), cU("w"));
	if (!outFile) return 1;

	/*SAPUNICODEOK_STRINGCONST*/ /*SAPUNICODEOK_LIBFCT*/
	fputs("<?xml version=\"1.0\"?>\n<message>", outFile);
	/*SAPUNICODEOK_LIBFCT*/
	fwrite(buffer, 1, utf8Len, outFile); // See comment above for system i
	/*SAPUNICODEOK_STRINGCONST*/ /*SAPUNICODEOK_LIBFCT*/
	fputs("</message>", outFile);
	fclose(outFile);

	// Now view the message.xml file in a standard browser that supports UTF-8, and you should
	// be able to view the Japanese characters.

	return 0;
}

