#include "startrfc.h"

int mainU (int argc, SAP_UC ** argv)
{
    OPTIONS options = {};
    if(!parseCommand(argc, argv, &options))
        return 0;
    if(!checkOptions(&options))
    {
        showHelp();
        return 1;
    }
    RFC_RC rc = startRfc(&options);
    return rc;
}

bool parseCommand(int argc, SAP_UC ** argv, OPTIONS* options)
{
    if( argc < 2 || !strcmpU(argv[1], cU("-help")) || !strcmpU(argv[1], cU("-?")))
    {
        showHelp();
        return false;
    }
    else if(!strcmpU(argv[1], cU("-v")))
    {
        showVersion();
        return false;
    }
    int i = 1;
    const SAP_UC * const PATHNAME = cU("PATHNAME=");
    const SAP_UC * const PORT = cU("PORT=");
    const size_t   PATHNAME_LEN = 9;
    const size_t   PORT_LEN =5;

    while(i < argc)
    {
        const SAP_UC ch1 = argv[i][0];
        const SAP_UC ch2 = argv[i++][1];
        if(ch1 == cU('-') && ch2) // we found an option
        {
            if(ch2 == cU('i'))
            {
                options->showSysInfo = true;
                continue;
            }
            if(i > argc - 1 || argv[i][0] == cU('-'))
            {
                continue;
            }
            switch (ch2)
            {
            case cU('h'):
                options->ashost = argv[i++];
                break;
            case cU('s'):
                options->sysnr = argv[i++];
                break;
            case cU('u'):
                options->user = argv[i++];
                break;
            case cU('p'):
                options->passwd = argv[i++];
                break;
            case cU('c'):
                options->client = argv[i++];
                break;
            case cU('l'):
                options->language = argv[i++];
                break;
            case cU('D'):
                options->dest = argv[i++];
                break;
            case cU('F'):
                options->function = argv[i++];
                break;
            case cU('E'):
                {
                    const SAP_UC *param = argv[i++];
                    if(!strncmpU(param, PATHNAME, PATHNAME_LEN))
                    {
                        options->path = param + PATHNAME_LEN;
                    }
                    else if(!strncmpU(param, PORT, PORT_LEN))
                    {
                        options->port = param + PORT_LEN;
                    }
                }
                break;
			case cU('t'):
                options->trace = argv[i++];
                break;
            default:
                i++;
                break;
            }
        }
    }
    return true;
}

bool checkOptions(OPTIONS *options)
{
    SAP_UC ch = cU('\0');
    const SAP_UC * const EDI_DATA_INCOMING = cU("EDI_DATA_INCOMING");
    const SAP_UC * const EDI_STATUS_INCOMING = cU("EDI_STATUS_INCOMING");
    const unsigned MAX_PATH_LEN = 100;
    const unsigned MAX_PORT_LEN = 10;

    if(!options->dest)
    {
        if(!options->ashost )
            ch = cU('h');
        else if(!options->sysnr)
            ch = cU('s');
        else if(!options->user)
            ch = cU('u');
        else if(!options->passwd)
            ch = cU('p');
        else if(!options->client)
            ch = cU('c');
        if(ch)
        {
            printfU(cU("Missing or invalid -%c option.\n"), ch);
            return false;
        }
    }
    if(!options->showSysInfo)
    {
        if((!options->function) ||
            (strcmpU(options->function,EDI_DATA_INCOMING) && 
            strcmpU(options->function,EDI_STATUS_INCOMING)))
        {
            printfU(cU("Missing or invalid -F option.\n"));
            return false;
        }

        if(!options->path || !options->path[0])
        {
            printfU(cU("Missing or invalid -E PATHNAME=  option.\n"));
            return false;
        }
        else if(strlenU(options->path) > MAX_PATH_LEN)
        {
            printfU(cU("Path specified by -E PATHNAME= excceeds the maximum length of 100. \n"));
            return false;
        }
        if(!options->port ||!options->port[0] )
        {
            printfU(cU("Missing or invalid -E PORT=  option.\n"));
            return false;
        }
        else if(strlenU(options->port) > MAX_PORT_LEN)
        {
            printfU(cU("Port name specified by -E PORT= excceeds the maximum length of 10. \n"));
            return false;
        }
   }
   return true;
}

RFC_RC startRfc(OPTIONS *options)
{
    RFC_RC rc = RFC_OK;
    RFC_ERROR_INFO error;
    memsetR(&error, 0, sizeofR(RFC_ERROR_INFO));
    RFC_CONNECTION_PARAMETER connParams[] = {
                                {cU("ashost"), options->ashost},
                                {cU("sysnr"), options->sysnr},
                                {cU("client"), options->client},
                                {cU("lang"), options->language ? options->language : cU("E")},
                                {cU("user"), options->user},
                                {cU("passwd"), options->passwd},
                                {cU("dest"), options->dest ? options->dest : cU("")},
								{cU("trace"), options->trace}};
    RFC_CONNECTION_HANDLE connHandle = RfcOpenConnection(connParams, 
                                        sizeofR(connParams) / sizeofR(RFC_CONNECTION_PARAMETER),
                                        &error);
    if(connHandle)
    {
        if(options->showSysInfo)
        {
            RFC_ATTRIBUTES attr;
            rc = RfcGetConnectionAttributes(connHandle, &attr, &error);
            showConnAttr(&attr);

        }
        else if(options->function)
        {
            RFC_FUNCTION_DESC_HANDLE funcDesc = getFunctionHandle(options->function);
      	    RFC_FUNCTION_HANDLE funcHandle = RfcCreateFunction(funcDesc, 0);

            RfcSetChars(funcHandle, cU("PATHNAME"), options->path, (unsigned)strlenU(options->path), 0);
            RfcSetChars(funcHandle, cU("PORT"), options->port, (unsigned)strlenU(options->port), 0);
            rc = RfcInvoke(connHandle, funcHandle, &error);
        }
        if(RFC_OK == rc)
        {
            RfcCloseConnection(connHandle, &error);
            return rc;
        }
    }
    printfU(cU("Error: %s\n"), error.message);
    return error.code;
}

RFC_FUNCTION_DESC_HANDLE getFunctionHandle(const SAP_UC* functionName)
{
    RFC_PARAMETER_DESC parDescPathname = { iU("PATHNAME"), RFCTYPE_CHAR, RFC_IMPORT,   100,  200,   0, 0, 0, 0, 0};
    RFC_PARAMETER_DESC parDescPort =     { iU("PORT"),     RFCTYPE_CHAR, RFC_IMPORT,   10,   20,   0, 0, 0, 0, 0};
    RFC_FUNCTION_DESC_HANDLE funcDesc = RfcCreateFunctionDesc(functionName, 0);
    RfcAddParameter(funcDesc, &parDescPathname, 0);
    RfcAddParameter(funcDesc, &parDescPort, 0);
    return funcDesc;
}


void showHelp( )
{
    const SAP_UC * const programName = cU("startrfc");
    printfU( cU("\nUsage: %s [options]\n"), programName );
    printfU( cU("Options:\n") );
    printfU( cU("  -h <ashost>          SAP application server to connect to\n") );
    printfU( cU("  -s <sysnr>           system number of the target SAP system\n") );
    printfU( cU("  -u <user>            user\n") );
    printfU( cU("  -p <passwd>          password\n") );
    printfU( cU("  -c <client>          client \n") );
    printfU( cU("  -l <language>        logon language\n") );
    printfU( cU("  -D <destination>     destination defined in RFC config file sapnwrfc.ini\n") );
    printfU( cU("  -F <function>        function module to be called, only EDI_DATA_INCOMING\n") );
    printfU( cU("                       or EDI_STATUS_INCOMING is supported\n") );
    printfU( cU("  -E PATHNAME=<path>   path, including file name, to EDI data file or status \n") );
    printfU( cU("                       file, with maximum length of 100 charachters\n") );
    printfU( cU("  -E PORT=<port name>  port name of the ALE/EDI interface with maximum   \n") );
    printfU( cU("                       length of 10 charachters\n") );
    printfU( cU("  -t <level>           set RFC tracelevel 0(off), 1(brief), 2(verbose) or 3(full)\n") );
    printfU( cU("  -help  or -?         display this help page\n") );
    printfU( cU("  -v                   display the version of the NWRFC library, the version\n") );
    printfU( cU("                       of the compiler used by SAP to build this program and\n") );
	printfU( cU("                       the version of startrfc\n") );
    printfU( cU("  -i                   connect to the target system and display the system info\n") );

}

void showConnAttr(RFC_ATTRIBUTES *attr)
{
    if(!attr)
        return;
    printfU(cU("SAP System ID: %s\n"),attr->sysId);
    printfU(cU("SAP System Number: %s\n"),attr->sysNumber);
    printfU(cU("Partner Host: %s\n"),attr->partnerHost);
    printfU(cU("Own Host: %s\n"),attr->host);
    printfU(cU("Partner System Release: %s\n"),attr->partnerRel);
    printfU(cU("Partner Kernel Release: %s\n"),attr->kernelRel);
    printfU(cU("Own Release: %s\n"),attr->rel);
    printfU(cU("Partner Codepage: %s\n"),attr->partnerCodepage);
    printfU(cU("Own Codepage: %s\n"),attr->codepage);
    printfU(cU("User: %s\n"),attr->user);
    printfU(cU("Client: %s\n"),attr->client);
    printfU(cU("Language: %s\n"),attr->language);
}



void showVersion()
{
    printfU (cU("NW RFC Library Version: %s\n"), RfcGetVersion(NULL, NULL, NULL));
    printfU (cU("Compiler Version:\n")
#if defined SAPonAIX
		cU("%04X (VVRR)\n"), __xlC__
#elif defined SAPonHP_UX
		cU("%06d (VVRRPP. %s Compiler)\n"),	/*yes, decimal here!*/
	#if defined __HP_cc
			__HP_cc, cU("C")
	#elif defined __HP_aCC
			__HP_aCC, cU("C++")
	#else
			0, cU("Unknown Version")
	#endif
#elif defined SAPonLINUX
		cU("%s\n"), cU(__VERSION__)
#elif defined SAPonNT
		cU("%09d (VVRRPPPPP. Microsoft (R) C/C++ Compiler)\n"), _MSC_FULL_VER		/*decimal!*/
#elif defined SAPonSUN
		cU("%03X (VRP. %s Compiler)\n"),
	#if defined __SUNPRO_C
			__SUNPRO_C, cU("C")
	#elif defined __SUNPRO_CC
			__SUNPRO_CC, cU("C++")
	#else
			0, cU("Unknown Version")
	#endif
#elif defined SAPonOS390
        cU("%08X (PVRRMMMM)\n"), __COMPILER_VER__
#else
		cU("%s\n"), cU("Version not available.")
#endif
	);
    printfU (cU("Startrfc Version: 2018-08-15\n"));
}

