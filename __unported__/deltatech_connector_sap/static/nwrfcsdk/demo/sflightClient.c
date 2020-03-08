#include <stdlib.h>
#include <stdio.h>
#include "sapnwrfc.h"

static RFC_FUNCTION_DESC_HANDLE bapiFlightGetlistDesc, bapiFlightGetdetailDesc, bapiCommitDesc,
		bapiFlbookingCreateDesc;
static 	RFC_FUNCTION_HANDLE bapiFlightGetlist, bapiFlightGetdetail, bapiCommit,
		bapiFlbookingCreate;

RFC_RC lookupMetaData(RFC_CONNECTION_HANDLE connection, RFC_ERROR_INFO* errorInfoP){

	printfU(cU("Caching DDIC metadata..."));
	bapiFlightGetlistDesc = RfcGetFunctionDesc(connection, cU("BAPI_FLIGHT_GETLIST"), errorInfoP);
	if (bapiFlightGetlistDesc == NULL) goto end;
	bapiFlightGetdetailDesc = RfcGetFunctionDesc(connection, cU("BAPI_FLIGHT_GETDETAIL"), errorInfoP);
	if (bapiFlightGetdetailDesc == NULL) goto end;
	bapiCommitDesc = RfcGetFunctionDesc(connection, cU("BAPI_TRANSACTION_COMMIT"), errorInfoP);
	if (bapiCommitDesc == NULL) goto end;
	bapiFlbookingCreateDesc = RfcGetFunctionDesc(connection, cU("BAPI_FLBOOKING_CREATEFROMDATA"), errorInfoP);
	if (bapiFlbookingCreateDesc == NULL) goto end;
	
	end: printfU(cU("  ...done\n"));
	return errorInfoP->code;
}

void errorHandling(RFC_RC rc, SAP_UC* description, RFC_ERROR_INFO* errorInfo, RFC_CONNECTION_HANDLE connection){
	printfU(cU("%s: %d\n"), description, rc);
	printfU(cU("%s: %s\n"), errorInfo->key, errorInfo->message);
	// It's better to close the TCP/IP connection cleanly, than to just let the
	// backend get a "Connection reset by peer" error...
	if (connection != NULL) RfcCloseConnection(connection, errorInfo);

	exit(1);
}

void printReturnTable(RFC_TABLE_HANDLE returnTable){
	 unsigned int tabLen, i;
     int	j;
	SAP_UC buffer[249];
	RFC_STRUCTURE_HANDLE line;

	RfcGetRowCount(returnTable, &tabLen, NULL);
	printfU(cU("\nReturn Messages:\n"));
	for (i=0; i<tabLen; i++){
		RfcMoveTo(returnTable, i, NULL);
		line = RfcGetCurrentRow(returnTable, NULL);
		for (j=248; j>=0; j--) buffer[j] = cU(' ');
		RfcGetChars(line, cU("TYPE"), buffer, 1, NULL);
		RfcGetChars(line, cU("ID"), buffer+2, 20, NULL);
		RfcGetChars(line, cU("NUMBER"), buffer+24, 3, NULL);
		RfcGetString(line, cU("MESSAGE"), buffer+29, 220, NULL, NULL);

		printfU(buffer);printfU(cU("\n"));
	}
	printfU(cU("\n"));
}

void printSelection(void){
	printfU(cU("\nPlease select an Airline:\n"));
	printfU(cU("AA     American Airlines\n"));
	printfU(cU("AB     Air Berlin\n"));
	printfU(cU("AC     Air Canada\n"));
	printfU(cU("AF     Air France\n"));
	printfU(cU("AZ     Alitalia\n"));
	printfU(cU("BA     British Airways\n"));
	printfU(cU("CO     Continental Airlines\n"));
	printfU(cU("DL     Delta Airlines\n"));
	printfU(cU("FJ     Air Pacific\n"));
	printfU(cU("JL     Japan Airlines\n"));
	printfU(cU("LH     Lufthansa\n"));
	printfU(cU("NG     Lauda Air\n"));
	printfU(cU("NW     Northwest Airlines\n"));
	printfU(cU("QF     Qantas Airways\n"));
	printfU(cU("SA     South African Air.\n"));
	printfU(cU("SQ     Singapore Airlines\n"));
	printfU(cU("SR     Swiss\n"));
	printfU(cU("UA     United Airlines\n"));
	printfU(cU("*      All\n> "));
}

void printFlightListTable(RFC_TABLE_HANDLE tableHandle){
	unsigned int tabLen, i;
	RFC_STRUCTURE_HANDLE tabLine;
	RFC_ERROR_INFO errorInfo;
	SAP_UC format[] = iU("|%.5d| %.20s| %.20s| %.20s| %.8s | %.6s | %.8s | %.6s | %.12s| %.3s |\n");

	RfcGetRowCount(tableHandle, &tabLen, &errorInfo);
	printfU(cU("Found %u connections:\n"), tabLen);

	printfU(cU("|No.  | Airline             | City from           | City to             | Date     | Time   | Arr.Date |Arr.Time| Price       | Curr|\n"));
	printfU(cU("--------------------------------------------------------------------------------------------------------------------------------------\n"));

	for (i=0; i<tabLen; i++){
		SAP_UC airline[20] = iU(""), cityfrom[20] = iU(""), cityto[20] = iU(""), currIso[3] = iU(""), price[25] = iU("");
		RFC_DATE date = iU(""), arrDate = iU("");
		RFC_TIME time = iU(""), arrTime = iU("");
		RfcMoveTo(tableHandle, i, &errorInfo);
		tabLine = RfcGetCurrentRow(tableHandle, &errorInfo);
		RfcGetChars(tabLine, cU("AIRLINE"), airline, 20, &errorInfo);
		RfcGetChars(tabLine, cU("CITYFROM"), cityfrom, 20, &errorInfo);
		RfcGetChars(tabLine, cU("CITYTO"), cityto, 20, &errorInfo);
		RfcGetDate(tabLine, cU("FLIGHTDATE"), date, &errorInfo);
		RfcGetTime(tabLine, cU("DEPTIME"), time, &errorInfo);
		RfcGetDate(tabLine, cU("ARRDATE"), arrDate, &errorInfo);
		RfcGetTime(tabLine, cU("ARRTIME"), arrTime, &errorInfo);
		RfcGetChars(tabLine, cU("PRICE"), price, 25, &errorInfo);
		RfcGetChars(tabLine, cU("CURR_ISO"), currIso, 3, &errorInfo);
		printfU(format, i, airline, cityfrom, cityto, date, time, arrDate, arrTime, price, currIso);
	}
}

int mainU(int argc, SAP_UC** argv){
  // commnad options: hostname sysnr user passwd client language
	RFC_RC rc = RFC_OK;
	RFC_CONNECTION_PARAMETER loginParams[6];
	RFC_ERROR_INFO errorInfo;
	RFC_CONNECTION_HANDLE connection;
	RFC_TABLE_HANDLE tableHandle;
	RFC_STRUCTURE_HANDLE tabLine, flightData;
	unsigned tabLen, i;
	SAP_UC airlineID[4], connectionID[5], temp[256];
	RFC_DATE date;
	RFC_INT number;

	loginParams[0].name = cU("ashost");	loginParams[0].value = argc > 1 ? argv[1] : cU("hostname");
	loginParams[1].name = cU("sysnr");	loginParams[1].value = argc > 2 ? argv[2] : cU("50");
	loginParams[2].name = cU("user");	loginParams[2].value = argc > 3 ? argv[3] : cU("user");
	loginParams[3].name = cU("passwd");	loginParams[3].value = argc > 4 ? argv[4] : cU("******");
	loginParams[4].name = cU("client");	loginParams[4].value = argc > 5 ? argv[5] : cU("800");
	loginParams[5].name = cU("lang");	loginParams[5].value = cU("EN");

	printfU(cU("Logging in..."));
	connection = RfcOpenConnection(loginParams, 6, &errorInfo);
	if (connection == NULL) errorHandling(rc, cU("Error during logon"), &errorInfo, NULL);
	printfU(cU("  ...done\n\n"));

	rc = lookupMetaData(connection, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error during metadata lookup"), &errorInfo, connection);

	bapiFlightGetlist = RfcCreateFunction(bapiFlightGetlistDesc, &errorInfo);

	startAllOver: printSelection();
    /*CCQ_SECURE_LIB_OK*/
	getsU(temp);

	// Now we are filling the inputs of BAPI_FLIGHT_GETLIST:
	if (strcmpU(cU("*"), temp)){
        /*CCQ_SECURE_LIB_OK*/
		rc = RfcSetChars(bapiFlightGetlist, cU("AIRLINE"), temp, strlenU(temp), &errorInfo);
		if (rc != RFC_OK) errorHandling(rc, cU("Error while setting AIRLINE"), &errorInfo, connection);
	}
	RfcSetInt(bapiFlightGetlist, cU("MAX_ROWS"), 100, &errorInfo);

	RfcGetTable(bapiFlightGetlist, cU("DATE_RANGE"), &tableHandle, &errorInfo);
	tabLine = RfcAppendNewRow(tableHandle, &errorInfo);
	RfcSetChars(tabLine, cU("SIGN"), cU("I"), 1, &errorInfo);
	RfcSetChars(tabLine, cU("OPTION"), cU("BT"), 2, &errorInfo);

	startDate: printfU(cU("\nPlease enter a start date (yyyymmdd):\n> "));
    /*CCQ_SECURE_LIB_OK*/
	getsU(temp);
    /*CCQ_SECURE_LIB_OK*/
	if (strlenU(temp) != 8) goto startDate;
	for (i=0; i<8; i++){
		if (isdigitU(temp[i]) == 0) goto startDate;
		date[i] = temp[i];
	}
	rc = RfcSetDate(tabLine, cU("LOW"), date, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error while setting LOW"), &errorInfo, connection);

	endDate: printfU(cU("\nPlease enter an end  date (yyyymmdd):\n> "));
    /*CCQ_SECURE_LIB_OK*/
	getsU(temp);
    /*CCQ_SECURE_LIB_OK*/
	if (strlenU(temp) != 8) goto endDate;
	for (i=0; i<8; i++){
		if (isdigitU(temp[i]) == 0) goto endDate;
		date[i] = temp[i];
	}
	rc = RfcSetDate(tabLine, cU("HIGH"), date, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error while setting HIGH"), &errorInfo, connection);

	// Inputs complete. Now let's call the thing:
	rc = RfcInvoke(connection, bapiFlightGetlist, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error while calling BAPI_FLIGHT_GETLIST"), &errorInfo, connection);

	// The RETURN table sometimes contains helpful error messages, so let's display it to the user
	RfcGetTable(bapiFlightGetlist, cU("RETURN"), &tableHandle, &errorInfo);
	printReturnTable(tableHandle);

	// Now display the results we got in FLIGHT_LIST. Or if there aren't any, give the user a chance to
	// change his/her selection criteria.
	RfcGetTable(bapiFlightGetlist, cU("FLIGHT_LIST"), &tableHandle, &errorInfo);
	RfcGetRowCount(tableHandle, &tabLen, &errorInfo);
	if (tabLen == 0) goto startAllOver;
	printFlightListTable(tableHandle);

	chooseCon: printfU(cU("\nPlease choose a connection (0 - %u)\n> "), tabLen-1);
	scanfU(cU("%u"), &i);
	fflush(stdin);
	if (i >= tabLen) goto chooseCon;

	// Now go to the selected line in FLIGHT_LIST, read the necessary fields and set
	// them as inputs for BAPI_FLIGHT_GETDETAIL.
	// We memorize AIRLINEID, CONNECTIONID and FLIGHTDATE, as we may need them again
	// further down, in case the user wants to book that flight.
	RfcMoveTo(tableHandle, i, &errorInfo);
	tabLine = RfcGetCurrentRow(tableHandle, &errorInfo);

	bapiFlightGetdetail = RfcCreateFunction(bapiFlightGetdetailDesc, &errorInfo);
	RfcGetString(tabLine, cU("AIRLINEID"), airlineID, 4, &i, &errorInfo);
	RfcSetChars(bapiFlightGetdetail, cU("AIRLINEID"), airlineID, i, &errorInfo);
	RfcGetString(tabLine, cU("CONNECTID"), connectionID, 5, &i, &errorInfo);
	RfcSetChars(bapiFlightGetdetail, cU("CONNECTIONID"), connectionID, i, &errorInfo);
	RfcGetDate(tabLine, cU("FLIGHTDATE"), date, &errorInfo);
	RfcSetDate(bapiFlightGetdetail, cU("FLIGHTDATE"), date, &errorInfo);

	printfU(cU("\nConnection ID for the chosen flight: %s\n"), connectionID);

	// After we are finished reading from the FLIGHT_LIST table, we can release all memory associated
	// with the BAPI_FLIGHT_GETLIST call:
	RfcDestroyFunction(bapiFlightGetlist, &errorInfo);

	// Now get the details for the selected flight:
	rc = RfcInvoke(connection, bapiFlightGetdetail, &errorInfo);
	if (rc != RFC_OK) errorHandling(rc, cU("Error while calling BAPI_FLIGHT_GETDETAIL"), &errorInfo, connection);

	RfcGetTable(bapiFlightGetdetail, cU("RETURN"), &tableHandle, &errorInfo);
	printReturnTable(tableHandle);

	// Print the details we got:
	RfcGetStructure(bapiFlightGetdetail, cU("ADDITIONAL_INFO"), &flightData, &errorInfo);
	RfcGetString(flightData, cU("FLIGHTTIME"), temp, 15, NULL, &errorInfo);
	printfU(cU("Flighttime: %s min\n"), temp);
	RfcGetString(flightData, cU("DISTANCE"), temp, 15, NULL, &errorInfo);
	printfU(cU("Distance  : %s\n"), temp);
	RfcGetString(flightData, cU("UNIT"), temp, 15, NULL, &errorInfo);
	printfU(cU("Unit      : %s\n"), temp);
	RfcGetString(flightData, cU("PLANETYPE"), temp, 15, NULL, &errorInfo);
	printfU(cU("Plane type: %s\n"), temp);

	// Display the number of available seats:
	RfcGetStructure(bapiFlightGetdetail, cU("AVAILIBILITY"), &flightData, &errorInfo);
	printfU(cU("\nAvailability:\n"));
	printfU(cU("          Total  Free\n"));
	RfcGetInt(flightData, cU("ECONOMAX"), &number, &errorInfo);
	printfU(cU("Economy:   %d"), number);
	RfcGetInt(flightData, cU("ECONOFREE"), &number, &errorInfo);
	printfU(cU("     %d\n"), number);
	RfcGetInt(flightData, cU("BUSINMAX"), &number, &errorInfo);
	printfU(cU("Business:   %d"), number);
	RfcGetInt(flightData, cU("BUSINFREE"), &number, &errorInfo);
	printfU(cU("      %d\n"), number);
	RfcGetInt(flightData, cU("FIRSTMAX"), &number, &errorInfo);
	printfU(cU("First Cl:   %d"), number);
	RfcGetInt(flightData, cU("FIRSTFREE"), &number, &errorInfo);
	printfU(cU("      %d\n"), number);

	RfcDestroyFunction(bapiFlightGetdetail, &errorInfo);

	printfU(cU("\nBook the flight? [y/n]\n> "));
    /*CCQ_SECURE_LIB_OK*/
	getsU(temp);
	if (strcmpU(cU("y"), temp) == 0){
		printfU(cU("\nPlease enter the Class: Business [C], Economy [Y], First Class [F]\n> "));
        /*CCQ_SECURE_LIB_OK*/
		getsU(temp);

		// If the user wants to have that flight, we need to call BAPI_FLBOOKING_CREATE
		// and fill the BOOKING_DATA structure with the values we memorized above.
		bapiFlbookingCreate = RfcCreateFunction(bapiFlbookingCreateDesc, &errorInfo);
		RfcGetStructure(bapiFlbookingCreate, cU("BOOKING_DATA"), &flightData, &errorInfo);
        /*CCQ_SECURE_LIB_OK*/
		RfcSetChars(flightData, cU("AIRLINEID"), airlineID, strlenU(airlineID), &errorInfo);
        /*CCQ_SECURE_LIB_OK*/
		RfcSetChars(flightData, cU("CONNECTID"), connectionID, strlenU(connectionID), &errorInfo);
		RfcSetDate(flightData, cU("FLIGHTDATE"), date, &errorInfo);
		RfcSetChars(flightData, cU("CLASS"), temp, 1, &errorInfo);
		RfcSetChars(flightData, cU("CUSTOMERID"), cU("00000001"), 8, &errorInfo);
		RfcSetChars(flightData, cU("AGENCYNUM"), cU("00000093"), 8, &errorInfo);

		rc = RfcInvoke(connection, bapiFlbookingCreate, &errorInfo);
		if (rc != RFC_OK) errorHandling(rc, cU("Error while calling BAPI_FLBOOKING_CREATE"), &errorInfo, connection);

		// To persist our booking in the database, we need to call BAPI_TRANSACTION_COMMIT:
		bapiCommit = RfcCreateFunction(bapiCommitDesc, &errorInfo);
		RfcSetChars(bapiCommit, cU("WAIT"), cU("X"), 1, &errorInfo);

		rc = RfcInvoke(connection, bapiCommit, &errorInfo);
		if (rc != RFC_OK) errorHandling(rc, cU("Error while calling BAPI_TRANSACTION_COMMIT"), &errorInfo, connection);

		// The BAPI returns the order number in the RETURN table.
		RfcGetTable(bapiFlbookingCreate, cU("RETURN"), &tableHandle, &errorInfo);
		printReturnTable(tableHandle);

		RfcDestroyFunction(bapiFlbookingCreate, &errorInfo);
		RfcDestroyFunction(bapiCommit, &errorInfo);
	}

	// We are done, so let's log out.
	RfcCloseConnection(connection, &errorInfo);
	return 0;
}
