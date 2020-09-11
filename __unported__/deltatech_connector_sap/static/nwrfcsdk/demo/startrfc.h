#ifndef STARTRFC_H
#define STARTRFC_H

#include "sapnwrfc.h"

typedef struct _options
{
    SAP_UC const * user ;
    SAP_UC const * passwd ;
    SAP_UC const * client ;
    SAP_UC const * language ;
    SAP_UC const * ashost ;
    SAP_UC const * sysnr ;
    SAP_UC const * dest ;
    SAP_UC const * function;
    SAP_UC const * path;
    SAP_UC const * port;
    SAP_UC const * trace;
    bool           showSysInfo; 
}OPTIONS;

void showHelp();
void showVersion();
bool parseCommand(int argc, SAP_UC ** argv, OPTIONS* options);
bool checkOptions(OPTIONS *options);
RFC_RC startRfc(OPTIONS *options);
RFC_FUNCTION_DESC_HANDLE getFunctionHandle(const SAP_UC* functionName);
void showConnAttr(RFC_ATTRIBUTES *attr);

#endif  /*STARTRFC_H*/
