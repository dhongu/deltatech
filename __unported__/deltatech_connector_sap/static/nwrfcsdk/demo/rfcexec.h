#include "sapnwrfc.h"
#include <vector>
#include <stdio.h>

#ifdef SAPonHP_UX
namespace std {}
#endif
using namespace std;


class RfcExecServer{
public:
	RfcExecServer(int argc, SAP_UC** argv);
	~RfcExecServer(void);

	void run(void);
	bool checkAuthorization(SAP_UC* user, SAP_UC* sysid, SAP_UC* client, SAP_UC* path, SAP_UC* caller);
	RFC_RC handleRequest(RFC_CONNECTION_HANDLE rfcHandle, RFC_FUNCTION_HANDLE funcHandle, RFC_ERROR_INFO *errorInfo);
	void openTrace(void);
	void closeTrace(void);
	void printTraceHeader(void);
	void trace(const SAP_UC* key, const SAP_UC* value, int indent=0);

	static void initMetadata(void);
	static void usage(SAP_UC* param);

	bool running;

	static RFC_FUNCTION_DESC_HANDLE rfc_exec;
	static RFC_FUNCTION_DESC_HANDLE rfc_pipe;

private:
	void parseCommandFile(const SAP_UC* filePath);

        std::vector<RFC_CONNECTION_PARAMETER> connectionParams;
	RFC_CONNECTION_HANDLE connection;
	SAP_UC system[9];
	bool registered;
	bool secureMode;
	vector<SAP_UC*> allowed;
	FILE* traceFile;
	bool backendRequestedTrace;
};
