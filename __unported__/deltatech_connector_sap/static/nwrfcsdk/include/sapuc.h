/* @(#) $Id: //bas/721_REL/src/include/sapuc.h#9 $ SAP*/
/* CCQ_CCU_FILE_OFF */ /* CCQ_COV_FILE_OFF */ /* CCQ_IPV6_SUPPORT_FILE_OK */ /* CCQ_USE_TIME_T_FILE_OK */
#ifndef SAPUC_H
#define SAPUC_H "$Id: //bas/721_REL/src/include/sapuc.h#9 $"

/*******************************************************************************
 * (c) Copyright SAP AG, Walldorf
 *
 *
 *              SSSS   AAA   PPPP          U   U   CCCC
 *             S      A   A  P   P         U   U  C
 *              SSS   AAAAA  PPPP          U   U  C
 *                 S  A   A  P             U   U  C
 *             SSSS   A   A  P      =====   UUU    CCCC
 *
 *
 * This is one of the central include files which should be included by all
 * SAP sources.
 *
 * Implementation of the system function interface for the R/3 Unicode
 * kernel.  The functions declared here are to replace those system
 * functions which handle variables of type char. The implementation
 * of the external functions is in nlsui?.c, ? = 1, 2, 3, ... and in
 * the project i18n/sapu16.  The Unicode specific behavior of the
 * functions is documented in flat/nlsuidoc.htm and flat/sapu16doc.htm .
 *
 ******************************************************************************/

/*-HISTORY----------------------------------------------------------------------
 * 02.10.2012 tm       add SAP_CESU8.
 * 17.02.2011 bs       add vsprintf_sU() and vsprintf_sR(); include <stdarg.h>
 * 25.10.2010 bs       restore previous signature of nlsui_initialize() to avoid
 *                     incompatibility in RFC SDK. Move storing of command line
 *                     to new function nlsui_store_cmdline().
 * 12.03.2009 bs       add SAPwith7BIT_UNICODE
 * 06.02.2009 bs       add parentheses to macro definition MAX_PATH_LN
 * 24.10.2008 lm       add HPUX_U16_OPTIMIZED functionality
 * 22.10.2008 bs       add nlsui_addIcuSearchPath(). 
 * 10.04.2008 bs       avoid ccQ warnings for strlenR() and other str*R() macros
 * 13.03.2008 bs       use own implementation of strtok_r on all platforms 
 * 22.08.2007 mau      add MAX_PATH_LN for SAPonNT
 * 07.12.2006 meb      link libsapu16 content statically into portlib
 * 29.10.2006 vv       added wchar.h on windows also in non-unicode case
 * 15.08.2006 bs       add TOUPPERU(), TOLOWERU() macros
 * 28.07.2006 strehle  added mkstempU and mkstempsU
 * 30.05.2006 bs       remove getenv_sU16(). It is not required by ccQ and not
 *                     used. We regard getenvU() already as secure.
 * 06.04.2006 bs       add some *R macros that were existing only as secure
 *                     variants *_sR
 * 10.11.2005 bs       ato*U16(): map it correctly to U16 functions also in the
 *                       non-Unicode case
 * 19.07.2005 bs       SAPwithICU_CAL: Calendar functionality from ICU
 * 09.06.2005 ps       restructure mainU to allow private code first
 * 26.04.2005 bs       enable loading of ICU by mainU() in the non-Unicode case
 * 20.04.2005 bs       allow loadIcu to return with error.
 * 08.04.2005 bs       reorganize initialization of Unicode interface in mainU
 * 04.02.2005 bs       remove strerror_s functions and getenv_sRFB
 * 12.01.2004 bs       SAPwithICU_COLL for non-Unicode
 * 14.12.2004 meb      activate U-literals on SUN C++ projects
 * 25.08.2004 meb      strtok_rU also for platforms without native strtok_r
 * 05.05.2004 meb      Reorg Step 13: apply new U/U16 naming scheme to all functions
 * 14.04.2004 meb      Reorg Step 12: end double compilation of nlsui1.c/nlsui3.c
 * 05.04.2004 cla      add low-surrogate check in mblenU
 * 04.03.2004 meb      introduce isxdigit0F analogue to isdigit09
 * 16.02.2004 meb      Reorg Step 9: cleanup printf/scanf functions
 * 11.02.2004 meb      Reorg Step 8: introduce macro SAP_UNAME to reduce
 *                                   separation UC/NUC
 * 05.02.2004 meb      Reorg Step 7: cleanup string functions
 * 02.02.2004 meb      use isdigit09 also in non Unicode case
 * 21.01.2004 bs       Make SAP_U2 and SAP_UTF16 identical
 * 18.12.2003 meb      Reorg Step 6: cleanup fwriteU
 *                                   fwriteU -> fwriteU16 -> u16_fwriteU16
 * 12.12.2003 meb      Reorg Step 2: U16 trace non Unicode
 * 11.12.2003 meb      Reorg Step 1: NLS trace independent of SAPwithUNICODE
 * 07.12.2003 bs       introduce MB_CUR_MAX_U, MB_CUR_MAX_NUC, MB_CUR_MAX_UC
 * 27.11.2003 bs       Remove check for stdlib.h (is included anyway)
 * 19.11.2003 bs       Stop using types SAP_UCS, SAP_U2S, SAP_U4S, SAP_UTF16S,
 *                     SAP_UTF8S to simplify the use of 'const' type qualifiers
 * 01.11.2003 mit      Correct an incorrect ifdef .. AS400
 *
 * ?          ?        <see p4 filelog>
 *
 * 05.08.2003 ms       add reentrant functions for hostnames and services
 * 04.08.2003 bs       simplify usage of __SAP_DLL_DECLSPEC
 * 29.07.2003 meb      memcpy with check for overlapping buffers (in debug mode)
 * 25.07.2003 bs       statU: make sure <sys/stat> is included before our
 *                     own declarations
 * 17.07.2003 bs       readdir_rU()
 * 28.03.2003 bs       __SAP_DLL_DECLSPEC for Unicode ctype functions (for ITS)
 * 26.03.2003 bs       make ICU normalization available
 * 26.11.2002 meb      Make sccsid/sccsidU thread-safe
 *                     Remove static buffer in convertSCCSID_w
 *                     Malloc pointer instead and stored it into static variable
 * 25.11.2002 meb      Remove hack for Fujitsu Compiler concerning include of
 *                     <wchar.h> vs <cwchar>
 * 11.11.2002 mit      Modifiy mblenU() to accept  0  instead of pointer
 * 06.11.2002 mit      Modifiy mblenU() from UCS-2 to
 *                     real UTF-16
 * 02.10.2002 iseries  SAP_E8 is "char" on PASE too.
 * 17.07.2002 meb      support AIX 5.1 32-bit compilation (wchar_t is 2-Byte)
 * 27.05.2002 ub       strtoupperU etc.
 * 21.05.2002 meb      arabic shaping
 * 12.04.2002 bs       reorganized SAPwithICU* macros
 * 13.03.2002 ub       loadU and nlistU deleted
 * 07.02.2002 ub       statU, lstatU corrected
 * 21.01.2002 ub       __cdecl for functions which are exported on NT.
 * 05.12.2001 bs       prepare ICU on OSF1
 * 30.10.2001 bd       os390 support dllload -> support dllloadU
 * 06.11.2001 ub       fget_strU etc.
 * 05.10.2001 bs       prepare ICU on NT
 * 04.10.2001 bs       remove strcollU() and strxfrmU()
 * 07.08.2001 meb      remove include <widec.h> used for Sun dbgU for C
 *                     compilation
 *                     <wchar.h> and <wctype.h> is enough
 *                     keep <widec.h> for C++ compilation because there are
 *                     inconsistencies with namespace std
 * 07.06.2001 bs       iU()
 * 18.05.2001 bs       mktempU()
 * 27.04.2001 hm       RFC-SDK only: add conversion wchar_t <> SAP_UC.
 * 06.04.2001 meb      mark printfU and similiar functions with special comment
 *                     PRINTFLIKE to enable ccQ to check format strings
 *                     redefine standard macro offsetoff for ccQ to mark it as
 *                     byte length
 * 04.04.2001 meb      load sapu16lib via mainU
 * 12.03.2001 bs       ICU on sun_64 and rs6000_64
 * 05.03.2001 bs       ICU on SunOS
 * 16.02.2001 bs       enable access to ICU i18n shared lib via mainU()
 * 13.02.2001 ub       strtollU(), strtoullU()
 * #50
 * 26.01.2001 meb      remove obsolete macros SAPccUu and SAPccUp
 * 19.01.2001 bs       use ICU for ctype U-functions on AIX and Linux
 * #39
 * 04.01.2001 meb      move SAPUNICODEOK comments in marco RAW2UC to end of cast
 *                     to avoid warnings if casted parameter exceeds one line
 * 03.01.2001 ub       snprintfU, vsnprintfU
 * #37
 * 20.12.2000 meb      on RS6000 compiling forward declaration struct tm fails
 *                     if <ctime> has been included before (compiler bug)
 *                     workaround: suppress declaring time.h if
 *                     CPP_USE_NEW_C_HEADERS is set on RS6000
 * #23
 * 08.12.2000 meb      correct parameter names for macro splitpathU
 * #22
 * 16.11.2000 meb      make usage of C standard library header and functions
 *                     compatible to C and C++ standard
 * #21
 * 12.10.2000 bs       add CAST_RAW2UC()
 * #17
 * 25.09.2000 bs       asctime_rU(), ctime_rU()
 * #11
 * 23.08.2000 meb      Add SAP_UC <-> SAP_UC_MB
 * #10
 * 26.07.2000 bs       strcasecmpU(), strncasecmpU()
 * #6
 * 17.07.2000 ub       Use UTF-16 (SAP_UC_is_UTF16_without_wchar) for SAPonLIN
 * #5
 * 12.07.2000 ub       Use our [f]putsU function on AIX; the first parameter
 *                     is const SAP_UC* ;
 * #4
 * 07.07.2000 ub       NlsuiTraceLevel, nlsui_set_trace()
 * #83
 * 06.07.2000 ub       Add a cast to wint_t for isxxxU and toupper/lowerU on NT.
 *                     Similar for strchrU.
 * #76
 * 15.06.2000 meb      hp_64 support dlopen -> support dlopenU
 * #75
 * 25.04.1000 bs       statvfsU()
 * #68
 * 22.03.2000 meb      Make the isxxxU and toupper/lowerU functions to macros
 *                     also when compiling on NT in unicode debug mode.
 *                     Reasons:
 *                     - Avoid creating different code in debug and release mode
 *                     - NT iswxxx functions can be called directly allthough
 *                       they expect wint_t as paramter instead of int, because
 *                       the conversion is done implicitly
 * 22.03.2000 meb      Use _waccess for accessU in unicode mode on NT
 * 22.03.2000 meb      Add an empty implementation of nlsui_initial_setlocale
 *                     for NT because currently there is not UTF8 locale,
 *                     but offering the function now will probably make it
 *                     easier to use UTF8 locale when it is available
 * #66
 * 09.03.2000 bs       Linux port, part 1: make the Unicode case compilable
 * #65
 * 01.03.2000 bs       strtokU() on AIX; forward declarations for some structs
 * #63
 * 29.02.2000 ub       ungetcU removed because it does not exist on NT
 * #60
 * 16.02.2000 meb      add _splitpathU for NT
 *                     remove errorneous trailing ; in
 *                     #define removeU and renameU for NT
 * #58
 * 05.01.2000 bs       ccQ treats mem..U() macros as functions
 * 30.11.1999 bs       introduce SAPccQ preprocessor flag
 * #54
 * 09.11.1999 meb      solve problems with U functions isascii, chdir, exec...
 *                     isascii: declare a prototype for ccQ on NT
 *                     chdir: declare chdirU additionally to _chdirU
 *                     exec... declare for NT
 *                     map getoptU in Unicode case on NT to an external
 *                     function like on other platforms
 *                     remove old separate ccQ part for ccQ version before 2.3
 * #51
 * 27.10.1999 meb      define _XOPEN_SOURCE always with a numeric value
 * 20.10.1999 bs       #undef SAP_UC_is_4B for ccQ
 * 06.10.1999 ub       environU for OS400 ASCII (Non-Unicode case)
 * #47
 * 24.09.1999 meb      avoid ccQ warning because of sapuc.h macros
 *                     replace char* in single byte branches with SAP_CHAR
 *                     use special ccQ definition for main, setvbufU
 * #46
 * 21.09.1999 meb      use PATH_MAX only if it is defined
 *                     use dummy definition for fgetsR for all ccQ versions
 * #45
 * 21.09.1999 meb      map SAP_UC_is_4B to SAP_UC_is_2B for all ccQ versions
 * #44
 * 08.09.1999 meb      add getpassU
 * #43
 * 08.09.1999 meb      begining with ccQ version 2.3.0 use same defintions for
 *                     normale compiler and ccQ
 * #40
 * 27.08.1999 meb      define sizeofR/U as sizeofccQ not as (size_t)4 when ccQ
 *                     is running to enable correct compile time compilations
 * #38
 * 09.08.1999 meb      remove #include <netdb.h> for SunOS
 *                     it is not needed and causes ccQ compiler errors on
 *                     SunOS 5.6 if only _POSIX_SOURCE is defined
 * #37
 * 06.08.1999 bs       #include "ntport.h" always (undo change #32)
 * #34
 * 19.07.1999 meb      fix forward declaration for struct DIR on NT
 *                     the underlying struct is named _DIR
 * #32
 * 15.07.1999 bs       #include "ntport.h" only if not C++; otherwise it is
 *                     enough to declare struct DIR;
 * #30
 * 18.06.1999 bs       SAPccU: p and u mode of ccU now see the same code
 *                     some str..U() functions names now usable as function  ptr
 * 14.05.1999 HJL      What string for unicode object file identification
 *                     inserted.
 * #27
 * 15.04.1999 bs       #include <wchar.h> on NT also in case of C++ compilation
 * #19
 * 31.03.1999 bs       #undef for all function names in SAPccU section
 * #18
 * 29.03.1999 bs       xdr_stringU: enable on HP-UX 11
 * #15
 * 19.03.1999 bs       #define SAP_UC_is_2B and similar switches for
 *                     internal use of ccU even if SAP_UC is 4 bytes long
 * #8
 * 18.02.1999 bs       always include <stdarg.h> in the Unicode case
 *-
 * 05.02.1999 tk       some corrections for AS/400
 *-
 * 28.11.1998 tk, fs   Functions for SAP_UC_is_UTF16_without_wchar added.
 *                     Support for Unicode on SUN.
 *                     HP_UX switch _INCLUDE_POSIX_SOURCE not necessary for
 *                     each Unicode compilation.
 *-
 * 24.11.1998 mit      SAP_E8 is "char" on OS/400 and "unsigned char" elsewhere.
 *            /else/   mainO4 enhanced.
 *-
 * 16.11.1998 mit      Move alternative character types from sapuc2.h to
 *                     sapuc.h . Now they can be used in other include
 *                     files for prototypes or field definitions.
 *                     For using data of these types, you still have to
 *                     include sapuc2.h .
 *-20.70
 * 09.10.98 ub         types in prototypes changed from wchar_t to
 *                     SAP_UC and SAP_CHAR;
 *                     Preprocessor switch SAP_UC_is_UTF16_without_wchar
 *                     introduced
 *-20.61
 * 22.09.98 js         main4U renamed to mainO4, static function removed
 * 16.09.98 bs         struct groupU, getgrdgid
 * 10.09.98 js         main4U - only for AS/400 command processing programs
 * 06.08.98 bs         return type of mem..U() is always SAP_UC*, not sometimes
 *                     void *. Three new function names on NT
 *-20.51
 * 23.07.98 bs         remove parentheses from some macro definitions: enable
 *                     usage in function pointers
 *-20.50
 * 23.06.98 ub         getoptU
 *-20.49
 * 05.06.98 ub         basic support for HP_UX
 *-20.48
 * 22.05.98 ub         fwriteU, freadU, putcharU, getcharU
 *-20.47
 *-20.46
 * 11.05.98 ub         mainU, main3U, environment
 *          bs         introduce preprocessor switch SAPccU
 *-20.45
 *          ub         printf, scanf, put, get family for NT and DEC OSF1.
 *                     Type WINT_T introduced as return type / argument
 *                     type of fgetcU, fputcU, tolowerU, toupperU,
 *                     isalnum,  ..., isxdigit.
 *-20.43
 * 10.03.98 bs         typedef of SAP_UC and some Unicode preprocessor
 *                     switches moved to saptypeb.h
 *-20.42
 * 04.03.98 ub         printf, scanf, putc, getc, puts, gets etc.
 *                     reorganized; implemented for AIX.
 *
 *          on         SAPonOS400
 *-20.41
 * 21.01.98 bs         enabled double inclusion of sapuc.h
 *-20.40
 * 20.01.98 bs         removed all SAPuses... switches
 *                     started re-implementation of prinf-like functions
 *                     according to the new specification
 *                     made the Unicode case compilable: no more #error for
 *                     missing functions, but dummy implementations in rscpw1.c
 *-20.39
 * 08.01.98 bs         preconversion to unsigned char will not take place:
 *                     remove SAPwithUCHAR and SAPwithSTDC_CHAR and all
 *                     casts to char* or SAP_UC*
 *                     remove also UNS_CH and the ..T() macros
 *-20.38
 * 17.12.97 bs         more parentheses: (SAP_UC*)f(x) -> ((SAP_UC*)f(x))
 *-20.35
 * 15.12.97 bs         treat functions for SAPonOS2_2x from o2port.h
 *                     like system functions
 *                     introduced precompiler switch SAPwithSTDC_CHAR
 *-20.34
 * 11.12.97 bs         Parentheses in macro definitions for all parameters
 *                     which are cast: (char*)s -> (char*)(s)
 *-20.32
 * 09.12.97 bs         sapuc3.h merged into sapuc.h; new preprocessor
 *                     switches: SAPuses... for the use of U-structures
 *-20.31
 * 03.12.97 bs         added U-macros and T-macros for the snc interface
 *-20.28
 * 26.11.97 bs         Casts in the ...U() -macros for the non-Unicode Kernel.
 *                     New type UNS_CH and new macros ...T() added.
 *                     They are identical to type SAP_UC and ...U() macros.
 *-20.27
 * 12.11.97 bs         no more double parentheses necessary for U-functions
 *                     with variable parameter list
 *-20.26
 * 11.11.97 bs         struct utsnameU moved from sapuc3.h (back in 20.31)
 *-20.23
 * 10.10.97 bs         macro SCCSID added
 *-20.21
 * 20.09.97 bs         SAPwithUCHAR added: typedef unsigned char SAP_UC
 *-20.19
 * 03.06.97 bs         I/O streams now handle always UCS2 Little Endian
 *                     Added mblenU(), redefinition of MB_CUR_MAX, etc.
 *                     Reorganized derived preprocessor switches
 *-20.18
 * 29.05.1997 mit      SAP_RAW moved to satypeb.h
 *-20.16
 * 07.05.97 bs         NT port for the case SAPwithUNICODE
 *-20.15
 * 16.04.97 bs         added macros memcpyR(), memsetR() etc.
 *-20.13
 * 07.03.97 bs         more new functions added
 *-20.10
 * 27.01.97 B. Schilling (bs)
 *                     Completely new coding; new naming convention:
 *                       system function      SAP function
 *                          name()        ->    nameU()
 *                     many new functions
 *-END-HISTORY----------------------------------------------------------------*/

/*-----------------------------------------------------------------------------
 * sapuc.h  - compilation switches
 *
 *  There are some compilations switches which have to be derived
 *  from the global switch SAPwithUNICODE and platform switches.
 *  For every platform that supports Unicode,  the following switches must
 *  be set:
 *
 *   SAP_UC_is_1B   or  SAP_UC_is_wchar  or  SAP_UC_is_UTF16_without_wchar
 *
 *                   WCHAR_is_UCS2 or WCHAR_is_UTF16 or WCHAR_is_UCS4
 *
 *  The typedef for SAP_UC (SAP_UC_is_...) has been made in saptypeb.h already.
 *  SAPwithICU is set for all platforms where we use the ICU shared libraries.
 *  The switch
 *    WCHAR_is_2B  or  WCHAR_is_4B
 *  is needed for the definition of SAP_UTF16 and thus also in the non-Unicode
 *  case.
 *  
 *  The SAPwithICU_* switches indicate that the corresponding ICU functionality 
 *  is available through the sapiculib. The exception is SAPwithICU_CTYPE which 
 *  is set only for Unicode and works without the sapiculib.  
 *
 *  SAPwithICU_I18N can be used to enforce loading of ICU via mainU() even in 
 *  non-Unicode programs. 
 *----------------------------------------------------------------------------*/

#if defined(SAPonAIX)   || \
    defined(SAPonHP_UX) || \
    defined(SAPonLIN)   || \
    defined(SAPonSUN)   || \
    defined(SAPonOSF1)  || \
    defined(SAPonOS390) || \
    (defined(SAPonOS400) && defined(SAPwithUNICODE) ) || \
    defined(SAPonNT)
  /* platforms where ICU is available */
  #if defined(SAPwithUNICODE)
    #define SAPwithICU_CTYPE
  #endif
  #define SAPwithICU_COLL
  #define SAPwithICU_BIDI
  #define SAPwithICU_SHAPING
  #define SAPwithICU_BREAK
  #define SAPwithICU_NORM
  #define SAPwithICU_TRANS
  #define SAPwithICU_IDNA
  #define SAPwithICU_CAL
#endif

#if defined(SAPwithICU_CTYPE)   || \
    defined(SAPwithICU_COLL)    || \
    defined(SAPwithICU_BIDI)    || \
    defined(SAPwithICU_SHAPING) || \
    defined(SAPwithICU_BREAK)   || \
    defined(SAPwithICU_NORM)    || \
    defined(SAPwithICU_TRANS)   || \
    defined(SAPwithICU_IDNA)    || \
    defined(SAPwithICU_CAL)
  #define SAPwithICU
#endif

#if defined( SAPwithICU_CTYPE ) || \
    defined( SAPwithICU_I18N )
  #define SAPwithNLSUI_INITIALIZE
#endif

#if defined(SAPwithUNICODE)
  #define SAPwithU16LIB
  #define SAPwithU16LIBLinked
#endif

#if !defined(SAPwithUNICODE)
  #define SAPwithOS_LOCALE
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h   - check compilation switches
 *
 * The case           #if defined(SAP_UC_is_1B)
 * is identical to    #if !defined(SAPwithUNICODE)
 *
 * The Unicode implementation is currently based on the type
 * --  wchar_t     if (sizeof(wchar_t)==2)
 * --  wchar_t     if (sizeof(wchar_t)==4)  and  SAP_UC_is_wchar
 * -- unsigned short    if (sizeof(wchar_t)==4)
 *                         and SAP_UC_is_UTF16_without_wchar
 *                         and SAP_UC is defined as unsigned short
 * --  wchar_t     if (sizeof(wchar_t)==4)
 *                         and SAP_UC_is_UTF16_without_wchar
 *                         and SAP_UC is defined as wchar_t ; this
 *                         is for temporary testing only.
 *
 *
 * SAP_UC_is_wchar or SAP_UC_is_UTF16_without_wchar
 * are defined in saptypeb.h .
 *
 * In sapuc.h we distinguish as follows:
 *
 * #ifndef SAPwithUNICODE
 *         ... /o    No Unicode   o/
 * #else
 *             /o    Unicode U-functions that are independent of
 *                   the definition of SAP_UC      o/
 *   #if defined(SAP_UC_is_wchar)
 *             /o    Unicode U-functions or macros that use wchar_t       o/
 *   #elif defined(SAP_UC_is_UTF16_without_wchar)
 *             /o    Unicode U-functions that are necessary in the case
 *                   that SAP_UC is not wchar_t                           o/
 *   #endif
 * #endif
 *
 *
 * Source code that depends on SAPwithUNICODE but not on the implementation
 * of Unicode should look like:
 *
 * #if defined(SAPwithUNICODE)
 *         ...
 * #else
 *         ...
 * #endif
 *
 *----------------------------------------------------------------------------*/


/*-----------------------------------------------------------------------------
 * sapuc.h   -   derive further compilation switches for convenience
 *
 *  Length of Unicode in bytes:     Little endian or big endian byte order:
 *
 *   SAP_UC_is_2B, SAP_UC_is_4B      SAP_UC_is_2B_L, SAP_UC_is_4B_B  etc.
 *
 *  What kind of Unicode is used:
 *
 *   SAP_UC_is_UCS2L    UCS-2, little endian format
 *   SAP_UC_is_UCS4B    UCS-4, big endian format
 *         etc.
 *
 * Remark: Using two bytes is regarded as identical to using either
 * UCS-2 or UTF-16. If it should become necessary to distinguish between
 * UCS-4 and 4-byte UCS2, the following case distinctions must be extended.
 *
 *----------------------------------------------------------------------------*/

#if defined(SAPwithUNICODE)
  #define SAP_UC_is_2B
  #define SAP_UC_is_UTF16
  #if defined(SAPwithINT_LITTLEENDIAN)
    #define SAP_UC_is_2B_L
    #define SAP_UC_is_UTF16_L
  #else
    #define SAP_UC_is_2B_B
    #define SAP_UC_is_UTF16_B
  #endif
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h   - further includes
 *
 * Via saptype.h most neccessary headers are known, including
 * <limits.h>, <stddef.h>, <stdio.h>, <stdlib.h>, and <string.h>
 *----------------------------------------------------------------------------*/
#include <stdarg.h>

#if defined(SAPwithUNICODE) || defined(SAPU16C_LIB)

  #if defined(CPP_USE_NEW_C_HEADERS)
    #include <cstdarg>
  #endif

  #ifdef SAPonNT
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
    #else
      #include <wchar.h>
    #endif
  #elif defined(SAPonOS400)       /* wchar.h does not include time.h. */
    #ifndef _POSIX_LOCALE
      #define _POSIX_LOCALE
    #endif
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      #include <cwctype>
      #include <clocale>
    #else
      #include <wchar.h>
      #include <wctype.h>
      #include <locale.h>
    #endif
      #include <dirent.h>
      #include <ifs.h>
      #include <time.h>
      #include <spawn.h>

  #elif defined(SAPonAIX)
    #ifndef _XOPEN_SOURCE
      #define not_XOPEN_SOURCE
      #define _XOPEN_SOURCE 1
    #endif
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      /* struct tm forward declaration does not work because of compiler bug */
      #define CPP_SUPPRESS_TM_FORWARD
    #else
      #include <wchar.h>
    #endif
    #ifdef not_XOPEN_SOURCE
      #undef _XOPEN_SOURCE
      #undef not_XOPEN_SOURCE
    #endif
    #include <dirent.h>

  #elif defined(SAPonOSF1)
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
    #else
      #include <wchar.h>
    #endif
    #include <dirent.h>

  #elif defined(SAPonHP_UX)
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      /* New compiler version seems to need the following (cf. AIX).
       * But this is just experimental (TODO).  d025846 2001-07-19 */
      #define CPP_SUPPRESS_TM_FORWARD
    #else
      #include <wchar.h>
    #endif
    #include <dirent.h>
    #ifndef _INCLUDE__STDC__
      #define not_INCLUDE__STDC__
      #define _INCLUDE__STDC__
    #endif
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <clocale>
    #else
      #include <locale.h>  /* this is necessary !        XXX? */
    #endif
    #ifdef not_INCLUDE__STDC__
      #undef _INCLUDE__STDC__
      #undef not_INCLUDE__STDC__
    #endif
    #if defined(_LOCALE_INCLUDED) && !defined(LC_CTYPE)
      #error "Something went wrong when #including <locale.h>"
    #endif

  #elif defined(SAPonSUN)
    #if defined(CPP_USE_NEW_C_HEADERS)
      /* This is just experimental (TODO), cf. AIX.  d025846 2001-11-20 */
      #define CPP_SUPPRESS_TM_FORWARD
    #endif
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      #include <clocale>
      #include <widec.h>
    #else
      #include <wchar.h>
      #include <locale.h>
    #endif
    #include <dirent.h>

  #elif defined(SAPonLIN)  || defined(SAPonDARWIN)
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      #include <cwctype>      /* isw..() */
    #else
      #include <wchar.h>
      #include <wctype.h>     /* isw..() */
    #endif
    #include <sys/types.h>  /* other platforms include it already in stdio.h */
    #include <dirent.h>

  #elif defined(SAPonOS390)
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      #include <cwctype>      /* isw..() */
    #else
      #include <wchar.h>
      #include <wctype.h>     /* isw..() */
    #endif
    #include <dirent.h>
    #include <dll.h>
    #include <spawn.h>

  #elif defined(SAPonRM600)
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
    #else
      #include <wchar.h>
    #endif
    #include <dirent.h>

  #else /* other platforms */
    #error "Please edit sapuc.h for this platform"
  #endif /* different platforms */

#else
  #define CPP_SUPPRESS_TM_FORWARD

  #ifdef SAPonNT
    /* 
     * d045374 ,29.10.2006
     * On windows, always include wchar.h, also in non-unicode case
     * as it declares wmemxxx() functions.
     */
    #if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
    #else
      #include <wchar.h>
    #endif
  #elif defined(SAPonDARWIN)
	#if defined(CPP_USE_NEW_C_HEADERS)
      #include <cwchar>
      #include <cwctype>      /* isw..() */
    #else
      #include <wchar.h>
      #include <wctype.h>     /* isw..() */
    #endif
  #endif

#endif /* SAPwithUNICODE */

#ifdef SAPccQ
  #if defined(CPP_USE_NEW_C_HEADERS)
    #include <cstdarg>
  #else
    #include <stdarg.h>
  #endif
  #undef  va_arg
  #define va_arg( p, type ) (((type *)0)[0])
  #undef  va_start
  #define va_start( list, parmN )
  #undef  va_end
  #define va_end( list )
#endif

/*-----------------------------------------------------------------------------
 * sapuc.h  -  Default system code page
 *----------------------------------------------------------------------------*/

#if defined(SAP_UC_is_1B)
  #ifdef SAPwithCHAR_EBCDIC
    #define SAP_SYS_CP_STR cU("0120")
    #define SAP_SYS_CP_C4  {cU('0'),cU('1'),cU('2'),cU('0')}
  #else /* ASCII */
    #define SAP_SYS_CP_STR cU("1100")
    #define SAP_SYS_CP_C4  {cU('1'),cU('1'),cU('0'),cU('0')}
  #endif
#elif defined(SAP_UC_is_UTF16_B)
    #define SAP_SYS_CP_STR cU("4102")
    #define SAP_SYS_CP_C4  {cU('4'),cU('1'),cU('0'),cU('2')}
#elif defined(SAP_UC_is_UTF16_L)
    #define SAP_SYS_CP_STR cU("4103")
    #define SAP_SYS_CP_C4  {cU('4'),cU('1'),cU('0'),cU('3')}
#else
 #error "SAP_UC_is_?"
#endif

/*-----------------------------------------------------------------------------
 * sapuc.h  -  Calling convention on MS Windows
 *             CDCL_U will be #undef'd at the end of sapuc.h
 *----------------------------------------------------------------------------*/
#ifdef SAPonNT
  #define CDCL_U  __cdecl
#else
  #define CDCL_U
#endif

/*-----------------------------------------------------------------------------
 * sapuc.h  -  DSO/DLL export specifications
 *----------------------------------------------------------------------------*/
#ifndef DECL_EXP
#   if defined(SAPonLIN) && defined(__GNUC__) && defined(GCC_HIDDEN_VISIBILITY)
#     define DECL_EXP __attribute__((visibility("default")))
#   else
#     define DECL_EXP
#   endif
#endif


/**********************************************************************/
/* SAP_UTF16:   character for Unicode UTF16                           */
/*--------------------------------------------------------------------*/
/* This type cannot be used to define a variable for a single         */
/* character !                                                        */
/* The size of this type is 16 bit.                                   */
/* The coding used is UTF16 (ISO 10646). The release of that          */
/* ISO norm is not specified here. It is the most recent release that */
/* is supported by SAP.                                               */
/* Comparison to SAP_U2: SAP_U2 should be used when surrogate support */
/* is explicitely exluded. Otherwise, use SAP_UTF16.                  */
/*--------------------------------------------------------------------*/
/* This type gives access to some generic functions, which are        */
/* handled differently on the different platforms, but give the same  */
/* result to all SAP applications.                                    */
/*    Classification of a single character:                           */
/*       <none. Processing is done using SAP_UC.>                     */
/*    Simple handling of zero terminated strings:                     */
/*       <none. Processing is done using SAP_UC.>                     */
/*    Conversion functions:                                           */
/*       SAP_UTF16_...                                                */
/*--------------------------------------------------------------------*/

#define UTF16Null ((SAP_UTF16)0)

#if defined(WCHAR_is_2B)
  typedef wchar_t   SAP_UTF16;
#elif defined(SAP_UC_is_char16)
  typedef char16_t  SAP_UTF16;
#else
  typedef SAP_USHORT   SAP_UTF16 ;
#endif

/* All other routines are in "sapuc2.h". */

/*-----------------------------------------------------------------------------
 * sapuc.h  -  Return type of fgetcU
 *----------------------------------------------------------------------------*/
/* We want that the following code works:
 *   int c;   c = fgetcU(f);   if (c==EOF) ...
 *  Under NT, wchar.h defines:
 *  typedef unsigned short wchar_t;
 *  typedef wchar_t wint_t;
 *  #define WEOF (wint_t)(0xFFFF)
 *  Now  WEOF != EOF !!!         We don't like this.
 *  So we use WINT_T and WINT_EOF instead.
 *  Outside sapuc.h and nlsui1.c it is not necessary to use WINT_T .
 */
#if defined(SAPwithUNICODE) && !defined(NLSUI_WINT_T)
                /* also for SAP_UC_is_UTF16_without_wchar */
  #define NLSUI_WINT_T
  #if defined(SAPonNT)
    typedef int WINT_T;
    #define WINT_EOF (-1)
                      /* Now WINT_EOF == EOF */
  #elif defined(SAPonUNIX) || defined(SAPonOS400)
    typedef wint_t WINT_T;
    #define WINT_EOF WEOF
  #else
    #error "type WINT_T not defined on this platform"
  #endif
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  - macro for a safe cast to SAP_UC/SAP_CHAR
 *
 * Special check in Unicode debug mode and only inside SAP (not in RFC SDK):
 * An error message will be written to stderr when the alignment is not
 * sufficient on all platforms. In addition, the process will be aborted.
 *----------------------------------------------------------------------------*/
#if defined(SAPwithUNICODE) && !defined(NDEBUG) && defined(SAPTYPE_H)
  externC DECL_EXP SAP_UC * CDCL_U nlsui_cast_raw2uc( const void *, const SAP_UC *, int );
  #define CAST_RAW2UC( x )   \
    /* SAPUNICODEOK_CAST_RAW2UC */ nlsui_cast_raw2uc( x, cU(__FILE__), __LINE__ )
  #define CAST_RAW2CHAR( x ) \
    /* SAPUNICODEOK_CAST_RAW2UC */ nlsui_cast_raw2uc( x, cU(__FILE__), __LINE__ )

#else /* not Unicode or opt */
  #define CAST_RAW2UC( x )   \
    ((SAP_UC *)(x)   /* SAPUNICODEOK_CAST *//* SAPUNICODEOK_CAST_RAW2UC */)
  #define CAST_RAW2CHAR( x ) \
    ((SAP_CHAR *)(x) /* SAPUNICODEOK_CAST *//* SAPUNICODEOK_CAST_RAW2UC */)

#endif

#ifndef SAP_IDENT

/* THIS IS THE OLD SCCSID / sccsidU METHOD.
 * IT IS ONLY VALID FOR OLD SOURCES THAT DO NOT DEFINE SAP_IDENT.
 * TO BE REMOVED WHEN ALL SOURCES DEFINE SAP_IDENT. */

/*-----------------------------------------------------------------------------
 * sapuc.h  -  The SCCSID macro
 *----------------------------------------------------------------------------*/
#define sccsidR   sccsid

#ifndef SAPwithUNICODE
  #define SCCSID  sccsid
  #define sccsidU sccsid     /* nicer name than SCCSID */

#else /* Now SAPwithUNICODE */
  /* Every object file will contain the static pointer sccsidU16.
   * When the sccsidU macro is used for the first time, we call malloc(),
   * convert the sccsid and store the pointer in sccsidU16.
   * If malloc() fails, we return a pointer to static memory.
   * ********* NOTE: free() will never be called! ************ */
  static const SAP_UC* sccsidU16 = NULL;
  #define SCCSID sccsidU
  /* convert sccsid to Unicode and store in sccsidU16 if not already done
     return sccsidU16 in any case */
  #define sccsidU (sccsidU16!=NULL ? sccsidU16 : (sccsidU16=ConvertSCCSID_w(sccsid)))
  /* ********* Do not call the following function directly! *********** */
  externC DECL_EXP const SAP_UC* CDCL_U ConvertSCCSID_w( const char *sccsid );
#endif

#endif /* SAP_IDENT */

/*-----------------------------------------------------------------------------
 * sapuc.h  -  macros for length calculations
 *----------------------------------------------------------------------------*/

#ifndef SAPwithUNICODE
  #define SAP_UC_LN          (1U)
  #define SAP_UC_SF          (0U)  /* shift factor: logarithm of SAP_UC_LN */
  #define SAP_UC_ALIGN_MASK  (0U)  /* # bits necessary to check alignment  */

#else
  #define SAP_UC_LN          (2U)
  #define SAP_UC_SF          (1U)
  #define SAP_UC_ALIGN_MASK  (1U)

#endif


#define sizeofR(par)         sizeof(par)

#ifndef SAPwithUNICODE
  #define sizeofU(par)       sizeof(par)
#else
  #define sizeofU(par)       (sizeofR(par)/sizeofR(SAP_UC))
#endif


/*----------------------------------------------------------------------------
 * sapuc.h  -  character constants and string constants
 *---------------------------------------------------------------------------*/
#define cNtoS(par)      cNtoS_HELP( par )
#define cNtoS_HELP(par) #par

#define cR(par)         par

#ifndef SAPwithUNICODE
  #define cU(par)       par
  #define iU(par)       par

#else /* SAPwithUNICODE */
  #define cU(par)         cU16(par)
  #define iU(par)         iU16(par)

#endif

  /* String literals can be written as L"abc" */
#define cU16(par)      cU16_HELP(par) /* if par is a macro, it must be ...    */
#define iU16(par)      iU16_HELP(par) /* ... resolved before the 'L' is added */

#if defined(WCHAR_is_2B)
  #define cU16_HELP(par) L##par
  #define iU16_HELP(par) L##par
#elif defined(SAPccQ)
  /* String literals can be written as u"abc" */
  #define cU16_HELP(par) u##par
  #define iU16_HELP(par) u##par
#elif defined(SAPwithoutUTF16_LITERALS)
  /* prepare for a special conversion tool */
  #define cU16_HELP(par) _U16_LIT_cU par
  #define iU16_HELP(par) _U16_LIT_iU par
#elif defined(SAPonSUN)
  /* String literals can be written as U"abc" */
  #define cU16_HELP(par) U##par
  #define iU16_HELP(par) U##par
#else
  /* String literals can be written as u"abc" */
  #define cU16_HELP(par) u##par
  #define iU16_HELP(par) u##par
#endif


/*----------------------------------------------------------------------------
 * sapuc.h  -  helper to declare/implement U/U16 functions libsapu16
 *---------------------------------------------------------------------------*/

/* SAP_UNAME: name switching between Unicode and NonUnicode compilation mode */
#ifdef SAPwithUNICODE
  #define SAP_UNAME(name)            name##U16
  #define SAP_UNAME_(name)           name##U16
  #define SAP_UNAME_UR(name)         name##U16
  #define SAP_UNAME_MEM_RET(name)    name##U16
  #define NUC_UC(name_nuc, name_uc)  name_uc
#else
  #define SAP_UNAME(name)            name
  #ifdef SAPonNT
    #define SAP_UNAME_(name)         _##name
  #else
    #define SAP_UNAME_(name)         name
  #endif
  #define SAP_UNAME_UR(name)         name##R
  #define SAP_UNAME_MEM_RET(name)    (SAP_CHAR*)name##R
  #define NUC_UC(name_nuc, name_uc)  name_nuc
#endif

/* NT_CAST: casts only required on NT */
#ifdef SAPonNT
  #define NT_CAST(type)              (type)
#else
  #define NT_CAST(type)
#endif

/* SAP_U16_PROTOTYPE: prototype of U16 function,
   build from RETURN type and TPARAM macro of function */
/* HLP macros are needed to avoid expansion of name if name is a macro */
#define SAP_U16_PROTOTYPE_HLP(nameU16)  externC DECL_EXP nameU16##_RETURN nameU16 nameU16##_TPARAMS;
#if defined(SAPonNT)
  #define SAP_U16_PROTOTYPE_UO_HLP(nameU16)
  #define SAP_U16_PROTOTYPE_UX_HLP(nameU16)
#elif defined(SAPonUNIX)
  #define SAP_U16_PROTOTYPE_UO_HLP(nameU16) SAP_U16_PROTOTYPE_HLP(nameU16)
  #define SAP_U16_PROTOTYPE_UX_HLP(nameU16) SAP_U16_PROTOTYPE_HLP(nameU16)
#elif defined(SAPonOS400)
  #define SAP_U16_PROTOTYPE_UO_HLP(nameU16) SAP_U16_PROTOTYPE_HLP(nameU16)
  #define SAP_U16_PROTOTYPE_UX_HLP(nameU16)
#endif
#define SAP_U16_PROTOTYPE_STDC_HLP(nameU16)    \
  BEGIN_NS_STD_C_HEADER                        \
    SAP_U16_PROTOTYPE_HLP(nameU16)             \
  END_NS_STD_C_HEADER

#define SAP_U16_PROTOTYPE_FLIKE_HLP(nameU16)   \
  externC DECL_EXP nameU16##_RETURN nameU16 nameU16##_TPARAMS

#define SAP_U16_PROTOTYPE_STAT(name)        static name##U16_RETURN name##U16 name##U16_TPARAMS;
#define SAP_U16_PROTOTYPE(name)             SAP_U16_PROTOTYPE_HLP(name##U16)
#define SAP_U16_PROTOTYPE_UO(name)          SAP_U16_PROTOTYPE_UO_HLP(name##U16)
#define SAP_U16_PROTOTYPE_UX(name)          SAP_U16_PROTOTYPE_UX_HLP(name##U16)
#define SAP_U16_PROTOTYPE_STDC(name)        SAP_U16_PROTOTYPE_STDC_HLP(name##U16)
#define SAP_U16_PROTOTYPE_FLIKE(name)       SAP_U16_PROTOTYPE_FLIKE_HLP(name##U16)

#ifdef SAPwithUNICODE
  #define SAP_U16_PROTOTYPE_UC(name)        SAP_U16_PROTOTYPE_HLP(name##U16)
  #define SAP_U16_PROTOTYPE_UO_UC(name)     SAP_U16_PROTOTYPE_UO_HLP(name##U16)
  #define SAP_U16_PROTOTYPE_STDC_UC(name)   SAP_U16_PROTOTYPE_STDC_HLP(name##U16)
#else
  #define SAP_U16_PROTOTYPE_UC(name)
  #define SAP_U16_PROTOTYPE_UO_UC(name)
  #define SAP_U16_PROTOTYPE_STDC_UC(name)
#endif





/*----------------------------------------------------------------------------
 * sapuc.h  -  macro to guarantee an unsigned char in the non-Unicode case
 *---------------------------------------------------------------------------*/
#ifndef SAPwithUNICODE
  #define U_CHAR(par)    ((unsigned char)(par))
#else
  #define U_CHAR(par)    (par)
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -  File identification (SAP_IDENT, SAP_IDENTN)
 *----------------------------------------------------------------------------*/
/* There are two possibilites:
 * (1) In a source file, define 
 *     #define SAP_IDENT "@(#) $Id: //bas/721_REL/src/include/sapuc.h#9 $"
 *     at top of the file (before(!) including sapuc.h).
 *     This identicfication is processed later in sapuc.h
 * (2) In a source file, use the macro
 *     SAP_IDENTN(name,"@(#) $Id: //bas/721_REL/src/include/sapuc.h#9 $")
 *     after(!) including saptype.h to define a identication string, that is
 *     not 'sccsid'. Please note: A semicolon must not be placed behind
 *     this macro call, because this would cause errors on pedantic ISO-C
 *     compliant compilers (e.g. on AIX).
 * The macro SCCSID is obsolete and must not be used with SAP_IDENT.
 * It is possible to define in each compilation unit one SAP_IDENT (for the
 * file itself) and several SAP_IDENTN (e.g. for includes) with different
 * names, all of the these names != "sccsid".
 *----------------------------------------------------------------------------*/

#if defined(SAPonLIN) && defined(__GNUC__)

   /* used: omit unused warning, don't optimize this string away */
#  define SAP_USED __attribute__ ((used))

   /* unused: omit unused warning, optimize this string away if unused */
#  define SAP_UNUSED __attribute__ ((unused))

   /* section: store identification string in special section */
#  if __GNUC_PREREQ(3,0)
#    define SAP_IDENT_SEC __attribute__ ((section(cR(".ident.SAP"))))
#    define SAP_IDENT_SEC_U16 __attribute__ ((section(cR(".ident.SAP.u16"))))
#  else
#    define SAP_IDENT_SEC
#    define SAP_IDENT_SEC_U16
#  endif

#else

#  define SAP_USED
#  define SAP_UNUSED
#  define SAP_IDENT_SEC
#  define SAP_IDENT_SEC_U16

#endif

#ifndef SAPwithUNICODE
#  define SAP_IDENTN(name,id) \
            static const SAP_RAW SAP_USED name[] SAP_IDENT_SEC = cR(id);
#else
#  define SAP_IDENTN(name,id) \
            static const SAP_RAW SAP_USED name[] SAP_IDENT_SEC = cR(id); \
            static const SAP_UC SAP_UNUSED name##U16[] SAP_IDENT_SEC_U16 = iU(id);
#endif

#ifdef SAP_IDENT

/* SAP_IDENT was defined before inclusion of sapuc.h, create sccsid here: */
SAP_IDENTN(sccsid, SAP_IDENT)

#  define sccsidR   sccsid

#  ifndef SAPwithUNICODE
#    define sccsidU (const SAP_UC *)sccsid  /* cast, SAP_RAW would not be useful */
#  else
#    define sccsidU (const SAP_UC *)sccsidU16
#  endif

#endif /* SAP_IDENT */

/*-----------------------------------------------------------------------------
 * sapuc.h  - 'what'-identifier definition for distinguishing unicode
 *            from non unicode object files.
 *----------------------------------------------------------------------------*/
#if SAP_RELEASE_NO >= 5010
  #ifdef SAPwithUNICODE
   static SAP_RAW SAP_UNUSED unicodeId[] = cR("@(#)     Unicode");
  #else
   static SAP_RAW SAP_UNUSED unicodeId[] = cR("@(#) non-Unicode");
  #endif
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  - Debug helper function that checks correct 2-byte alignment of
 *            strings. Calls to this function will be inserted automatically
 *            by the u16lit parser.
 *----------------------------------------------------------------------------*/

externC SAP_UTF16 * dbgAlignCheckStringU16( char * ); /* _never_ change that "char *" ! */

/*-----------------------------------------------------------------------------
 * sapuc.h  -   Function that counts number of bytes to write
 *----------------------------------------------------------------------------*/

#ifndef SAPwithUNICODE
  #define UcnToFileLenR(data, n)  (n)
#else
  externC size_tR CDCL_U UcnToFileLenR( SAP_CHAR *data, size_tU n );
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -  Functions for string handling:  str...
 * There are ...R macros available whenever the corresponding secure library
 * ..._sR function name is also defined.
 * 
 * The comments SAPUNICODEOK_LIBFCT can be removed again as soon as 
 * ccQ knows these function names. 
 *----------------------------------------------------------------------------*/

#define strcatR( dest, src )        /*SAPUNICODEOK_LIBFCT*/ strcat( dest, src )
#define strcatU16_RETURN            SAP_UTF16*
#define strcatU16_TPARAMS           (SAP_UTF16 * dest, const SAP_UTF16 * src)
#define strcatU16_PARAMS            (dest, src)
SAP_U16_PROTOTYPE_STDC(strcat)
#define strcatU                     SAP_UNAME(strcat)

#define strchrU16_RETURN            SAP_UTF16*
#define strchrU16_TPARAMS           (const SAP_UTF16 * wcs, int c)
#define strchrU16_PARAMS            (wcs, c)
SAP_U16_PROTOTYPE_STDC(strchr)
#define strchrU(  s,  c  )          SAP_UNAME(strchr)( s, U_CHAR(c) )

#define strcmpU16_RETURN            int
#define strcmpU16_TPARAMS           (const SAP_UTF16 *s1, const SAP_UTF16 *s2)
#define strcmpU16_PARAMS            (s1, s2)
SAP_U16_PROTOTYPE_STDC(strcmp)
#define strcmpU                     SAP_UNAME(strcmp)

#define strcpyR( dest, src )        /*SAPUNICODEOK_LIBFCT*/ strcpy( dest, src )
#define strcpyU16_RETURN            SAP_UTF16*
#define strcpyU16_TPARAMS           (SAP_UTF16 * dest, const SAP_UTF16 * src)
#define strcpyU16_PARAMS            (dest, src)
SAP_U16_PROTOTYPE_STDC(strcpy)
#define strcpyU                     SAP_UNAME(strcpy)

#define strcspnU16_RETURN           size_t
#define strcspnU16_TPARAMS          (const SAP_UTF16* ucs, const SAP_UTF16* reject)
#define strcspnU16_PARAMS           (ucs, reject)
SAP_U16_PROTOTYPE_STDC(strcspn)
#define strcspnU                    SAP_UNAME(strcspn)

#define strdupU16_RETURN            SAP_UTF16*
#define strdupU16_TPARAMS           (const SAP_UTF16 * s)
#define strdupU16_PARAMS            (s)
SAP_U16_PROTOTYPE_STDC(strdup)
#define _strdupU                    SAP_UNAME_(strdup)
#define strdupU                     SAP_UNAME(strdup)

#define strlenR( s )                /*SAPUNICODEOK_LIBFCT*/ strlen( s )
#define strlenU16_RETURN            size_t
#define strlenU16_TPARAMS           (const SAP_UTF16 *s)
#define strlenU16_PARAMS            (s)
SAP_U16_PROTOTYPE_STDC(strlen)
#define strlenU                     SAP_UNAME(strlen)

#define strncatR( dest, src, n )    /*SAPUNICODEOK_LIBFCT*/ strncat( dest, src, n )
#define strncatU16_RETURN           SAP_UTF16*
#define strncatU16_TPARAMS          (SAP_UTF16 * dest, const SAP_UTF16 * src, size_t n)
#define strncatU16_PARAMS           (dest, src, n)
SAP_U16_PROTOTYPE_STDC(strncat)
#define strncatU                    SAP_UNAME(strncat)

#define strncmpU16_RETURN           int
#define strncmpU16_TPARAMS          (const SAP_UTF16 * s1, const SAP_UTF16 * s2, size_t n)
#define strncmpU16_PARAMS           (s1, s2, n)
SAP_U16_PROTOTYPE_STDC(strncmp)
#define strncmpU                    SAP_UNAME(strncmp)

#define strncpyR( dest, src, n )    /*SAPUNICODEOK_LIBFCT*/ strncpy( dest, src, n )
#define strncpyU16_RETURN           SAP_UTF16*
#define strncpyU16_TPARAMS          (SAP_UTF16 * dest, const SAP_UTF16 * src, size_t n)
#define strncpyU16_PARAMS           (dest, src, n)
SAP_U16_PROTOTYPE_STDC(strncpy)
#define strncpyU                    SAP_UNAME(strncpy)

#define strpbrkU16_RETURN           SAP_UTF16*
#define strpbrkU16_TPARAMS          (const SAP_UTF16 * ucs, const SAP_UTF16 * accept)
#define strpbrkU16_PARAMS           (ucs, accept)
SAP_U16_PROTOTYPE_STDC(strpbrk)
#define strpbrkU                    SAP_UNAME(strpbrk)

#define strrchrU16_RETURN           SAP_UTF16*
#define strrchrU16_TPARAMS          (const SAP_UTF16 * wcs, int c)
#define strrchrU16_PARAMS           (wcs, c)
SAP_U16_PROTOTYPE_STDC(strrchr)
#define strrchrU( s,  c  )          SAP_UNAME(strrchr)( s, U_CHAR(c) )

#define strspnU16_RETURN            size_t
#define strspnU16_TPARAMS           (const SAP_UTF16 * ucs, const SAP_UTF16 * accept)
#define strspnU16_PARAMS            (ucs, accept)
SAP_U16_PROTOTYPE_STDC(strspn)
#define strspnU                     SAP_UNAME(strspn)

#define strstrU16_RETURN            SAP_UTF16*
#define strstrU16_TPARAMS           (const SAP_UTF16 * haystack, const SAP_UTF16 * needle)
#define strstrU16_PARAMS            (haystack, needle)
SAP_U16_PROTOTYPE_STDC(strstr)
#define strstrU                     SAP_UNAME(strstr)

#define strtokU16_RETURN            SAP_UTF16*
#define strtokU16_TPARAMS           (SAP_UTF16 * s, const SAP_UTF16 * delim)
#define strtokU16_PARAMS            (s, delim)
SAP_U16_PROTOTYPE_STDC(strtok)
#define strtokU                     SAP_UNAME(strtok)

/* We use our own implementation of strtok_r() on all platforms. This makes the 
 * availability of strtok_rU() independent of platform specific macros 
 */
externC DECL_EXP char* strtok_rRFB( char* s, const char* delim, char** save_ptr);
#define strtok_rR strtok_rRFB

#define strtok_rU16_RETURN          SAP_UTF16*
#define strtok_rU16_TPARAMS         (SAP_UTF16 * s, const SAP_UTF16 * delim, SAP_UTF16 **save_ptr)
#define strtok_rU16_PARAMS          (s, delim, save_ptr)
SAP_U16_PROTOTYPE_STDC(strtok_r)
#define strtok_rU                   SAP_UNAME_UR(strtok_r)

#if defined(WCHAR_is_2B)
  #define strcatU16                       wcscat
  #ifdef SAPonNT    /* Cast to avoid warning (d025846) */
    #define strchrU16(  s,  c  )          wcschr(  s,  (wchar_t)(c) )
    #define strrchrU16( s1, c  )          wcsrchr( s1, (wchar_t)(c) )
  #else
    #define strchrU16                     wcschr
    #define strrchrU16                    wcsrchr
  #endif
  #define strcmpU16                       wcscmp
  #define strcpyU16                       wcscpy
  #define strcspnU16                      wcscspn
  #ifdef SAPonNT
     #define _strdupU16                   _wcsdup
     #define strdupU16                    _wcsdup
  #endif
  #define strlenU16                       wcslen
  #define strncatU16                      wcsncat
  #define strncmpU16                      wcsncmp
  #define strncpyU16                      wcsncpy
  #define strpbrkU16                      wcspbrk
  #define strspnU16                       wcsspn
  #define strstrU16                       wcswcs
  #if defined (SAPonNT)
    #define strtokU16                     wcstok
    /* strtok_r does not exist on NT */
  #endif
#endif

/*-----------------------------------------------------------------------------------*/
#ifdef SAPonOS400
  #if ( ( ! defined (__EXTENDED__) ) || ( ! defined ( __cplusplus ) ) )
    #pragma datamodel(P128)
    /* for some weird reason IBM only defines certain string functions for C++ in its */
    /* header files */
    /* the following lines are copied from string.h from a V5R1 machine */
    char *strdup(const char *);
    char *strnset(char *, int c, size_t);
    char *strset(char *, int c);
    #pragma map(strdup, "__strdup")
    #pragma map(strnset, "__strnset")
    #pragma map(strset, "__strset")
    #pragma datamodel(pop)
  #endif
#endif /* SAPonOS400 */

/*-----------------------------------------------------------------------------
 * sapuc.h  -  Functions for string handling:  str to number
 *
 *----------------------------------------------------------------------------*/

#define strtodU16_RETURN            double
#define strtodU16_TPARAMS           (const SAP_UTF16 *str, SAP_UTF16 **endptr)
#define strtodU16_PARAMS            (str, endptr)
SAP_U16_PROTOTYPE_STDC(strtod)
#define strtodU(  s, end )          SAP_UNAME(strtod)(  s,  end )

#define strtolU16_RETURN            long
#define strtolU16_TPARAMS           (const SAP_UTF16 *s, SAP_UTF16 **end, int base)
#define strtolU16_PARAMS            (s, end, base)
SAP_U16_PROTOTYPE_STDC(strtol)
#define strtolU( s, end, base )     SAP_UNAME(strtol)(  s,  end, base )

#define strtoulU16_RETURN           unsigned long
#define strtoulU16_TPARAMS          (const SAP_UTF16 *s, SAP_UTF16 **end, int base)
#define strtoulU16_PARAMS           (s, end, base)
SAP_U16_PROTOTYPE_STDC(strtoul)
#define strtoulU( s, end, base )    SAP_UNAME(strtoul)(  s,  end, base )

#define strtollU16_RETURN           long long
#define strtollU16_TPARAMS          (const SAP_UTF16 *s, SAP_UTF16 **end, int base)
#define strtollU16_PARAMS           (s, end, base)
SAP_U16_PROTOTYPE_STDC_UC(strtoll)

#define strtoullU16_RETURN          unsigned long long
#define strtoullU16_TPARAMS         (const SAP_UTF16 *s, SAP_UTF16 **end, int base)
#define strtoullU16_PARAMS          (s, end, base)
SAP_U16_PROTOTYPE_STDC_UC(strtoull)

#ifdef SAPonNT
  #define strtollU(  s, end, base )     NUC_UC(_strtoi64,strtollU16)(  s, end, base )
  #define strtoullU( s, end, base )     NUC_UC(_strtoui64,strtoullU16)( s, end, base )
#else
/* ATTENTION: strtoll() and strtoull() do not yet exist on some platforms,
 * e.g. HP-UX 11.00. */
  #define strtollU(  s,  end, base )    SAP_UNAME(strtoll)(  s,  end, base )
  #define strtoullU( s,  end, base )    SAP_UNAME(strtoull)( s,  end, base )
#endif


#if defined(WCHAR_is_2B)
  #define strtodU16( s, end )             wcstod( s, end )
  #define strtolU16(  s, end, base )      wcstol(  s, end, base )
  #define strtoulU16( s, end, base )      wcstoul( s, end, base )
  #ifdef SAPonNT
    #define strtollU16(  s, end, base )   _wcstoi64(  s, end, base )
    #define strtoullU16( s, end, base )   _wcstoui64( s, end, base )
  #else
    #define strtollU16(  s, end, base )   wcstoll(  s, end, base )
    #define strtoullU16( s, end, base )   wcstoull( s, end, base )
  #endif
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -  Functions for string handling:  case
 *
 *----------------------------------------------------------------------------*/

#define strcasecmpU16_RETURN            int
#define strcasecmpU16_TPARAMS           (const SAP_UTF16* s1, const SAP_UTF16* s2)
#define strcasecmpU16_PARAMS            (s1, s2)
SAP_U16_PROTOTYPE(strcasecmp)
externC int strcasecmpR                 (const char * s1, const char * s2);
#define strcasecmpU(s1, s2)             SAP_UNAME_UR(strcasecmp)(s1, s2)

#define strncasecmpU16_RETURN           int
#define strncasecmpU16_TPARAMS          (const SAP_UTF16* s1, const SAP_UTF16* s2, size_tU n)
#define strncasecmpU16_PARAMS           (s1, s2,n)
SAP_U16_PROTOTYPE(strncasecmp)
externC DECL_EXP int strncasecmpR (const char * s1, const char * s2, size_t n);
#define strncasecmpU(s1, s2, n)         SAP_UNAME_UR(strncasecmp)(s1, s2, n)

externC DECL_EXP SAP_UTF16 * strtoupperU16 (SAP_UTF16 * s1);
externC DECL_EXP char * strtoupperR     (char * s1);
#define strtoupperU(s1)                 SAP_UNAME_UR(strtoupper)(s1)

externC DECL_EXP SAP_UTF16 * strtolowerU16 (SAP_UTF16 * s1);
externC DECL_EXP char * strtolowerR     (char * s1);
#define strtolowerU(s1)                 SAP_UNAME_UR(strtolower)(s1)

externC DECL_EXP SAP_UTF16 * strntoupperU16 (SAP_UTF16 * s1, size_tU len );
externC DECL_EXP char * strntoupperR    (char * s1, size_tU len);
#define strntoupperU(s1,len)            SAP_UNAME_UR(strntoupper)(s1,len)

externC DECL_EXP SAP_UTF16 * strntolowerU16 (SAP_UTF16 * s1, size_tU len );
externC DECL_EXP char * strntolowerR    (char * s1, size_tU len);
#define strntolowerU(s1,len)            SAP_UNAME_UR(strntolower)(s1,len)

externC DECL_EXP SAP_UTF16 * strcpytoupperU16 (SAP_UTF16 * dst, const SAP_UTF16 * src );
externC DECL_EXP char * strcpytoupperR  (char * dst, const char * src );
#define strcpytoupperU(dst,src)         SAP_UNAME_UR(strcpytoupper)(dst,src)

externC DECL_EXP SAP_UTF16 * strcpytolowerU16 (SAP_UTF16 * dst, const SAP_UTF16 * src );
externC DECL_EXP char * strcpytolowerR  (char * dst, const char * src );
#define strcpytolowerU(dst,src)         SAP_UNAME_UR(strcpytolower)(dst,src)

#ifdef SAPonNT
  #define _strcmpiU(  s1, s2 )          NUC_UC(_strcmpi,_wcsicmp)(  s1, s2 )
  #define strcmpiU(   s1, s2 )          NUC_UC(_strcmpi,_wcsicmp)(  s1, s2 )
  #define _stricmpU(  s1, s2 )          NUC_UC(_stricmp,_wcsicmp)(  s1, s2 )
  #define stricmpU(   s1, s2 )          NUC_UC(_stricmp,_wcsicmp)(  s1, s2 )
  #define _strnicmpU( s1, s2, n )       NUC_UC(_strnicmp,_wcsnicmp)( s1, s2, n )
  #define strnicmpU(  s1, s2, n )       NUC_UC(_strnicmp,_wcsnicmp)( s1, s2, n )
#elif defined(SAPonOS400)
  #define strcmpiU( s1, s2 )           strcasecmpU(  s1, s2 )
  #define stricmpU( s1, s2 )           strcasecmpU(  s1, s2 )
  #define strnicmpU( s1, s2, n )       strncasecmpU( s1, s2, n )
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h - functions for string handling: conversion to numeric types
 *----------------------------------------------------------------------------*/

#if defined(WCHAR_is_2B)

  #define atoiU16(s)                 ((int)wcstol(s, (SAP_UTF16 **)0, 10))
  #define atofU16(s)                 wcstod(s, (SAP_UTF16 **)0)
  #define atolU16(s)                 wcstol(s, (SAP_UTF16 **)0, 10)
  #if defined(SAPonNT)
    #define atollU16(s)              _wtoi64(s)
  #else
    #define atollU16(s)              wcstoll(s, (SAP_UTF16 **)0, 10)
  #endif /* !SAPonNT */

#else

  #define atoiU16(s)                 ((int)strtolU16(s, (SAP_UTF16 **)0, 10))
  #define atofU16(s)                 strtodU16(s, (SAP_UTF16 **)0)
  #define atolU16(s)                 strtolU16(s, (SAP_UTF16 **)0, 10)
  #define atollU16(s)                strtollU16(s, (SAP_UTF16 **)0, 10)

#endif

#define atoiU(s)                   SAP_UNAME(atoi)(s)
#define atofU(s)                   SAP_UNAME(atof)(s)
#define atolU(s)                   SAP_UNAME(atol)(s)
#if defined(SAPonNT)
  #define atollU(s)                NUC_UC(_atoi64,atollU16)(s)
#elif defined(SAPonHP_UX) && !defined(atoll)
  /* there is no atoll available in older releases of HP-UX*/
  #define atollU(s)                NUC_UC(atol,atollU16)(s)
#else
  #define atollU(s)                SAP_UNAME(atoll)(s)
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h - further functions for string handling
 *----------------------------------------------------------------------------*/
#ifndef SAPwithUNICODE

  #define getoptU(ac, av, op)        getopt(ac, av, op)
  /* In NT's C runtime lib, there is no getopt.
   * There are several getopt clones in the R/3 sources, and for NT the
   * obove #define is necessary in order to be able to use such a clone
   */
  #define optargU                    optarg

#else /* Now SAPwithUNICODE */

  externC int CDCL_U getoptU(int argc, SAP_UC * const argv[], const SAP_UC * optstr);

  /* __SAP_DLL_DECLSPEC for NT, as optargU is data pointer. See more comment below. */
  externC __SAP_DLL_DECLSPEC SAP_UC *optargU;

#endif


#if defined(SAPwithPASE400) && !defined(SAPccQ)
  /* on OS/400, a forked job can be given a name - so we use forkU there */
  #define forkU(name) fork400_ex(name)
#elif defined(SAPonLIN) && !defined(SAPccQ)
  /* on Linux we redefine fork to be able to do performance analysis */
  #define forkU(name) fork_Linux ( name )
#else
  #define forkU(name) fork()
#endif

/*-----------------------------------------------------------------------------
 * sapuc.h - Memory operations
 *
 * The macros memcmpR(), memcpyR(), memmoveR(), etc. should  be
 * used in those cases where the length parameter counts the number
 * of bytes even in a Unicode system.
 *----------------------------------------------------------------------------*/

#define mallocR                   malloc
#define mallocU16( len )          ((SAP_UTF16 *) malloc( (len)*sizeofR(SAP_UTF16)))
#define mallocU( len )            (SAP_UNAME_MEM_RET(malloc)( len ))

#define reallocR                  realloc
#define reallocU16( s, len )      ((SAP_UTF16 *) realloc( s, (len)*sizeofR(SAP_UTF16)))
#define reallocU( s,      len )   (SAP_UNAME_MEM_RET(realloc)( s, len ))

#define callocR                   calloc
#define callocU16( num, len )     ((SAP_UTF16 *) calloc( num, (len)*sizeofR(SAP_UTF16)))
#define callocU(  number, len )   (SAP_UNAME_MEM_RET(calloc)(  number, len ))

#define memcmpR                   memcmp
#define memcmpU16_RETURN          int
#define memcmpU16_TPARAMS         (const SAP_UTF16 * s1, const SAP_UTF16 * s2, size_t n)
#define memcmpU16_PARAMS          (s1, s2, n)
SAP_U16_PROTOTYPE(memcmp)
#define memcmpU(  s1, s2, len )   SAP_UNAME_UR(memcmp)( s1, s2, len )
#define memcpyR                   memcpy
#define memcpyU(  s1, s2, len )   (SAP_UNAME_MEM_RET(memcpy)(  s1, s2, len ))

#define memmoveR                  memmove
#define memmoveU( s1, s2, len )   (SAP_UNAME_MEM_RET(memmove)( s1, s2, len ))

#define memchrR                   memchr
#define memchrU16_RETURN          SAP_UTF16 *
#define memchrU16_TPARAMS         ( const SAP_UTF16 * s, int c, size_t n)
#define memchrU16_PARAMS          ( s, c, n )
SAP_U16_PROTOTYPE(memchr)
#define memchrU(  s,  c,  len )   (SAP_UNAME_MEM_RET(memchr)(  s, U_CHAR(c), len ))

#define memsetU_GCC( s, c, len )  { SAP_UC* _mr = (__builtin_constant_p(c) && (SAP_UC_LN == 2) \
				     && ((c) & 0xff) == (((c)>>8) & 0xff) )		\
				   ? ((SAP_UC*) memsetR(s, c, (len)*SAP_UC_LN))		\
				   : (SAP_UNAME_MEM_RET(memset)( s, U_CHAR(c), len ));	\
				   (_mr); }

#define memsetR                   memset
#define memsetU16_RETURN          SAP_UTF16*
#define memsetU16_TPARAMS         (SAP_UTF16 * s, int c, size_t n)
#define memsetU16_PARAMS          (s, c, n)
SAP_U16_PROTOTYPE(memset)
#if defined(SAPonLIN) && defined(__GNUC__) && !defined(SAPccQ)
# define memsetU(  s,  c,  len )   (memsetU_GCC( s, c, len ))
#else
# define memsetU(  s,  c,  len )   (SAP_UNAME_MEM_RET(memset)(  s, U_CHAR(c), len ) )
#endif

#if defined(SAPwithPASE400) && defined(SAPwithUNICODE) && defined(EXT_RELEASE)
  #undef memsetU
  #ifdef __cplusplus
	extern "C"
  #endif
  SAP_UTF16* memsetUTF16_blocked(SAP_UTF16 *dest, SAP_UTF16 c, size_t count);
  #define memsetU16PASE(dest,c,count)																	\
          (!(c) ? (SAP_UTF16 *)/*SAPUNICODEOK_CONVERSION*/memsetR((dest),0,(count)*sizeofR(SAP_UTF16))  \
                : ((count) <= 8) ? memsetU16((dest),(c),(count))										\
                                 : memsetUTF16_blocked((dest),(c),(count)))
  #define memsetU memsetU16PASE
#endif

#define bzeroR                    bzero
#define bzeroU16( s, len )        memsetU16( s, (WINT_T)0, len )
#define bzeroU( s, len )          SAP_UNAME_UR(bzero)( s, len )

#if ( defined(SAPonOS400)                        || \
     (defined(SAPonNT))     )
    /* on these platforms there are wmem..() functions available */
    #define memcmpU16(  s1, s2, len )  wmemcmp(  s1, s2, len )
    #define memcpyU16(  s1, s2, len )  wmemcpy(  s1, s2, len )
    #define memmoveU16( s1, s2, len )  wmemmove( s1, s2, len )
    #define memchrU16(  s,  wc, len )  wmemchr(  s,  wc, len )
    #define memsetU16(  s,  wc, len )  wmemset(  s,  wc, len )

#else  /* SAP_UC is not wchar_t or no wmem...() functions are available:
          * use own implementations; either macros or the external functions
          * declared above or functions from libsapu16.
          */
  #if defined(SAPwithINT_BIGENDIAN) && !defined(SAPonLIN)
     #define       memcmpU16(   s1, s2, len )             \
                   memcmp(    s1, s2, (len)*sizeofR(SAP_UTF16) )
  #endif
  #define          memcpyU16(  s1, s2, len )              \
       ((SAP_UTF16*)memcpy(   s1, s2, (len)*sizeofR(SAP_UTF16) ))
  #define          memmoveU16( s1, s2, len )              \
       ((SAP_UTF16*)memmove(  s1, s2, (len)*sizeofR(SAP_UTF16) ))

  #if defined(HPUX_U16_OPTIMIZED)
     #ifdef __cplusplus
       extern "C" { void *__memsetU16(void *s, int c, size_t n); }
     #else
       void *__memsetU16(void *s, int c, size_t n);
     #endif

     #define memsetU16(  s,  wc, len )  __memsetU16(  s,  wc, len )
  #endif

#endif

#if defined(SAPccQ) && defined(SAPwithUNICODE)
  /* for len check ccQ requires that the memU... functions are
     declared as functions
     therefore undef macros to make function declarations behind visible */
  #undef mallocU16
  externC SAP_UTF16 * mallocU16  ( size_tU );
  #undef reallocU16
  externC SAP_UTF16 * reallocU16 ( SAP_UTF16 *,                    size_tU );
  #undef callocU16
  externC SAP_UTF16 * callocU16  ( size_t,                         size_tU );
  #undef memcpyU16
  externC SAP_UTF16 * memcpyU16  ( SAP_UTF16 *, const SAP_UTF16 *, size_tU );
  #undef memmoveU16
  externC SAP_UTF16 * memmoveU16 ( SAP_UTF16 *, const SAP_UTF16 *, size_tU );
  #undef memchrU16
  #undef memsetU16
  #undef memcmpU16

  /* treat offesetof as byte length */
  #undef offsetof
  #define offsetof(s,m)   ((size_tR)1)

#endif


/*-----------------------------------------------------------------------------
 * sapuc.h - Functions that handle type char pointers (no string handling):
 *          1. functions that pass a type char pointer
 *              to the non-unicode world
 *----------------------------------------------------------------------------*/


#if defined(SAPonSUN) || defined(SAPonSINIX) || defined(SAPonOSF1) \
      || defined (SAPonLIN) || defined(SAPonAIX) || defined(SAPonPTX) \
      || ( defined(SAPonHP_UX) && defined(SAPwith64_BIT) ) \
      || ( defined(SAPonOS390) && defined(_UNIX03_SOURCE) ) \
      || defined (SAPonDARW)
  #define dlopenU16_RETURN             void*
  #define dlopenU16_TPARAMS            (const SAP_UTF16* path, int mode)
  #define dlopenU16_PARAMS             (path, mode)
  SAP_U16_PROTOTYPE(dlopen)
  #define dlopenU(path, mode)          SAP_UNAME(dlopen)(path, mode)

  #define dlsymU16_RETURN              void*
  #define dlsymU16_TPARAMS             (void *handle, const SAP_UTF16 *name)
  #define dlsymU16_PARAMS              (handle, name)
  SAP_U16_PROTOTYPE(dlsym)
  #define dlsymU(handle, name)         SAP_UNAME(dlsym)(handle, name)

  #define dlerrorU16_RETURN            SAP_UTF16*
  #define dlerrorU16_TPARAMS           (void)
  #define dlerrorU16_PARAMS            ()
  SAP_U16_PROTOTYPE(dlerror)
  #define dlerrorU                     SAP_UNAME(dlerror)

#endif

#if defined(SAPonHP_UX) && defined(_DL_INCLUDED)

  #define shl_loadU16_RETURN           shl_t
  #define shl_loadU16_TPARAMS          (const SAP_UTF16 *path, int  flags, long address)
  #define shl_loadU16_PARAMS           (path, flags, address)
  SAP_U16_PROTOTYPE(shl_load)
  #define shl_loadU(path, flags, address) \
                                       SAP_UNAME(shl_load)(path, flags, address)

  #define shl_findsymU16_RETURN        int
  #define shl_findsymU16_TPARAMS       (shl_t *handle, const SAP_UTF16 *sym, \
                                        short  type,   void *value)
  #define shl_findsymU16_PARAMS        (handle, sym, type, value)
  SAP_U16_PROTOTYPE(shl_findsym)
  #define shl_findsymU(handle, sym, type, value) \
                                       SAP_UNAME(shl_findsym)(handle, sym, type, value)

#endif

#if defined(SAPonOS390)
  #define dllloadU16_RETURN            void*
  #define dllloadU16_TPARAMS           (const SAP_UTF16 *path)
  #define dllloadU16_PARAMS            (path)
  SAP_U16_PROTOTYPE(dllload)
  #define dllloadU(path)               SAP_UNAME(dllload)(path)

  #define dllqueryfnU16_RETURN         void*
  #define dllqueryfnU16_TPARAMS        (dllhandle *handle, const SAP_UTF16 *sym)
  #define dllqueryfnU16_PARAMS         (handle, sym)
  SAP_U16_PROTOTYPE_UC(dllqueryfn)
  #define dllqueryfnU(handle, sym)     SAP_UNAME(dllqueryfn)(handle, sym)
#endif /* SAPonOS390 */

#define accessU16_RETURN               int
#define accessU16_TPARAMS              (const SAP_UTF16 *path, int mode )
#define accessU16_PARAMS               (path, mode)
SAP_U16_PROTOTYPE(access)
#define accessU(path, mode)            SAP_UNAME(access)(path, mode)

#define chdirU16_RETURN                int
#define chdirU16_TPARAMS               (const SAP_UTF16 *path)
#define chdirU16_PARAMS                (path)
SAP_U16_PROTOTYPE(chdir)
#define chdirU(path)                   SAP_UNAME(chdir)(path)

#define fdopenU16_RETURN               FILE*
#define fdopenU16_TPARAMS              (int filedes, const SAP_UTF16 *type)
#define fdopenU16_PARAMS               (filedes, type)
SAP_U16_PROTOTYPE_STDC(fdopen)
#define fdopenU(filedes, type)         SAP_UNAME(fdopen)(filedes, type)

#define fopenU16_RETURN                FILE*
#define fopenU16_TPARAMS               (const SAP_UTF16 *path, const SAP_UTF16 *mode)
#define fopenU16_PARAMS                (path, mode)
SAP_U16_PROTOTYPE_STDC(fopen)
#define fopenU(path, mode)             SAP_UNAME(fopen)(path, mode)

#if !defined(SAPonNT) && !defined(SAPonOSF1)
  #define fopen64U16_RETURN            FILE*
  #define fopen64U16_TPARAMS           (const SAP_UTF16 *path, const SAP_UTF16 *mode)
  #define fopen64U16_PARAMS            (path, mode)
  SAP_U16_PROTOTYPE_STDC(fopen64)
  #define fopen64U(path, mode)         SAP_UNAME(fopen64)(path, mode)
#endif

#define freopenU16_RETURN              FILE*
#define freopenU16_TPARAMS             (const SAP_UTF16 *path, const SAP_UTF16 *mode, \
                                        FILE *stream)
#define freopenU16_PARAMS              (path, mode, stream)
SAP_U16_PROTOTYPE_STDC(freopen)
#define freopenU(path, mode, stream)   SAP_UNAME(freopen)(path, mode, stream)

#define gethostnameU16_RETURN          int
#define gethostnameU16_TPARAMS         (SAP_UTF16 * name, size_tU len )
#define gethostnameU16_PARAMS          (name, len)
SAP_U16_PROTOTYPE(gethostname)
#define gethostnameU(name, len)        SAP_UNAME(gethostname)(name, len)

#define openU16_RETURN                 int
#define openU16_TPARAMS                (const SAP_UTF16 *wpath, int oflag, ... )
#define openU16_PARAMS                 (wpath, oflag, rest_args )
SAP_U16_PROTOTYPE(open)
#define openU                          SAP_UNAME_(open)
#define _openU                         openU

#define perrorU16_RETURN               void
#define perrorU16_TPARAMS              (const SAP_UTF16 *program)
#define perrorU16_PARAMS               (program)
SAP_U16_PROTOTYPE_STDC(perror)
#define perrorU(program)               SAP_UNAME(perror)(program)

#define popenU16_RETURN                FILE*
#define popenU16_TPARAMS               (const SAP_UTF16 *wcomm, const SAP_UTF16 *wtype)
#define popenU16_PARAMS                (wcomm, wtype)
SAP_U16_PROTOTYPE(popen)
#define popenU(command, type)          SAP_UNAME_(popen)(command, type)
#define _popenU(command, type)         popenU(command, type)

#define removeU16_RETURN               int
#define removeU16_TPARAMS              (const SAP_UTF16 *path)
#define removeU16_PARAMS               (path)
SAP_U16_PROTOTYPE_STDC(remove)
#define removeU(path)                  SAP_UNAME(remove)(path)

#define renameU16_RETURN               int
#define renameU16_TPARAMS              (const SAP_UTF16 *from, const SAP_UTF16 *to)
#define renameU16_PARAMS               (from, to)
SAP_U16_PROTOTYPE_STDC(rename)
#define renameU(from, to)              SAP_UNAME(rename)(from, to)

#define rmdirU16_RETURN                 int
#define rmdirU16_TPARAMS                (const SAP_UTF16 *wpath)
#define rmdirU16_PARAMS                 (wpath)
SAP_U16_PROTOTYPE(rmdir)
#define rmdirU(path)                    SAP_UNAME_(rmdir)(path)

#define systemU16_RETURN               int
#define systemU16_TPARAMS              (const SAP_UTF16 *s)
#define systemU16_PARAMS               (s)
SAP_U16_PROTOTYPE(system)
#define systemU(s)                     SAP_UNAME(system)(s)

#if !defined(CPP_SUPPRESS_TM_FORWARD)
   struct tm;
#endif
#define strftimeU16_RETURN             size_t
#define strftimeU16_TPARAMS            (SAP_UTF16 *wcs, size_t len, const SAP_UTF16 *format, \
                                       const struct tm *tmdate)
#define strftimeU16_PARAMS             (wcs, len, format, tmdate)
SAP_U16_PROTOTYPE_STDC_UC(strftime)
#define strftimeU(s, maxsize, format, tptr) \
                                       SAP_UNAME(strftime)(s, maxsize, format, tptr)

#define unlinkU16_RETURN               int
#define unlinkU16_TPARAMS              (const SAP_UTF16 *path)
#define unlinkU16_PARAMS               (path)
SAP_U16_PROTOTYPE(unlink)
#define unlinkU(path)                  SAP_UNAME_(unlink)(path)
#define _unlinkU(path)                 unlinkU(path)

struct utimbuf;
#define utimeU16_RETURN                int
#define utimeU16_TPARAMS               (const SAP_UTF16 *wpath, const struct utimbuf *time)
#define utimeU16_PARAMS                (wpath, time)
SAP_U16_PROTOTYPE(utime)
#define utimeU(path, time)             SAP_UNAME_(utime)(path, time)

#if ((!defined(SAPonHP_UX)) || defined(_MODE_T)) && \
    !defined(SAPonNT) &&                            \
    defined(SAPwithUNICODE)
  #define SAP_U16_PROTOTYPE_MODE_T(name)         SAP_U16_PROTOTYPE_HLP(name##U16)
#else
  #define SAP_U16_PROTOTYPE_MODE_T(name)
#endif

#define chmodU16_RETURN                int
#define chmodU16_TPARAMS               (const SAP_UTF16 *wpath, mode_t mode)
#define chmodU16_PARAMS                (wpath, mode)
SAP_U16_PROTOTYPE_MODE_T(chmod)
#define chmodU(wpath, mode)            SAP_UNAME_(chmod)(wpath, mode)
#define _chmodU(wpath, mode)           chmodU(wpath, mode)

#define creatU16_RETURN                int
#define creatU16_TPARAMS               (const SAP_UTF16 *wpath, mode_t mode)
#define creatU16_PARAMS                (wpath, mode)
SAP_U16_PROTOTYPE_MODE_T(creat)
#define creatU(wpath, mode)            SAP_UNAME_(creat)(wpath, mode)

#define mkdirU16_RETURN                int
#define mkdirU16_TPARAMS               (const SAP_UTF16 *wpath, mode_t mode)
#define mkdirU16_PARAMS                (wpath, mode)
SAP_U16_PROTOTYPE_MODE_T(mkdir)
#ifdef SAPonNT
  #define _mkdirU(wpath)               SAP_UNAME(_mkdir)(wpath)
#else
  #define mkdirU(wpath, mode)          SAP_UNAME(mkdir)(wpath, mode)
#endif

/*
 * map mkstempsU in the moment only to SAP own implementation
 * SAP_mkstemps. If there are later platform specific implementaions
 * available then switch here between the variants.
 */
externC int SAP_mkstemps(SAP_UC* tmpl, int suffix_len);
#define mkstempsU(tmpl,suffix_len)   SAP_mkstemps(tmpl,suffix_len)

#ifdef SAPonNT
  #define mkstempU( tmpl )             mkstemp( tmpl )
#elif defined(SAPonOS400)
  #define mkstempU( tmpl ) mkstempsU(tmpl,0)
#else
  #define mkstempU16_RETURN            int
  #define mkstempU16_TPARAMS           (SAP_UTF16 *tmpl)
  #define mkstempU16_PARAMS            (tmpl)
  SAP_U16_PROTOTYPE_STDC(mkstemp)
  #define mkstempU(tmpl)               SAP_UNAME(mkstemp)(tmpl)
#endif

/*
 * add mkstempsR for raw file creation
 */
externC int SAP_mkstempsR(SAP_RAW* tmpl, int suffix_len);
#define mkstempsR(tmpl,suffix_len)   SAP_mkstempsR(tmpl,suffix_len)
#if defined(SAPonOS400)
  #define mkstempR( tmpl ) mkstempsR(tmpl,0) 
#endif

#ifndef SAPonNT
  #define mkfifoU16_RETURN             int
  #define mkfifoU16_TPARAMS            (const SAP_UTF16 *wpath, mode_t mode)
  #define mkfifoU16_PARAMS             (wpath, mode)
  SAP_U16_PROTOTYPE_MODE_T(mkfifo)
  #define mkfifoU(wpath, mode)         SAP_UNAME(mkfifo)(wpath, mode)
#endif

#if defined(SAPonUNIX) || defined(SAPonOS400)

  #define chownU16_RETURN             int
  #define chownU16_TPARAMS            (const SAP_UTF16 *path, SAP_UINT owner, SAP_UINT group)
  #define chownU16_PARAMS             (path, owner, group)
  SAP_U16_PROTOTYPE(chown)
  #define chownU(path, owner, group)  SAP_UNAME(chown)(path, owner, group)

  #define linkU16_RETURN              int
  #define linkU16_TPARAMS             (const SAP_UTF16 *path1, const SAP_UTF16 *path2)
  #define linkU16_PARAMS              (path1, path2)
  SAP_U16_PROTOTYPE(link)
  #define linkU(path1, path2)         SAP_UNAME(link)(path1, path2)

  #define readlinkU16_RETURN          int
  #define readlinkU16_TPARAMS         (const SAP_UTF16 *path, SAP_UTF16 *buf, \
                                       NS_STD_C_HEADER size_t size)
  #define readlinkU16_PARAMS          (path, buf, size)
  SAP_U16_PROTOTYPE(readlink)
  #define readlinkU(path, buf, size)  SAP_UNAME(readlink)(path, buf, size)

  #define symlinkU16_RETURN           int
  #define symlinkU16_TPARAMS          (const SAP_UTF16 *path1, const SAP_UTF16 *path2)
  #define symlinkU16_PARAMS           (path1, path2)
  SAP_U16_PROTOTYPE(symlink)
  #define symlinkU(path1, path2)      SAP_UNAME(symlink)(path1, path2)

#endif

#if defined(SAPonNT)
  #define accessU16                   _waccess
  #define chdirU16                    _wchdir
  #define chmodU16                    _wchmod
  #define fdopenU16                   _wfdopen
  #define removeU16                   _wremove
  #define renameU16                   _wrename
  #define rmdirU16                    _wrmdir
  #define strftimeU16                 wcsftime
  #define systemU16                   _wsystem
  #define utimeU16                    _wutime
  #define unlinkU16                   _wunlink
  #define creatU16                    _wcreat
  #define _mkdirU16                   _wmkdir
  #define popenU16                    _wpopen
#elif defined(SAPonOS400)
  #define strftimeU16                 wcsftime
#endif

/* Modifications to support 64-Bit time_t */
#if defined(SAPonOS400) && defined(EXT_RELEASE)
  #include <sys/types.h>
  #if defined(__time64_t)
	#include <time.h>
	#include <utime.h>
	#include <sys/stat.h>
	#include <sys/sem.h>
	#include <sys/shm.h>
	#undef  time_t
	#define time_t time64_t
	#undef  ctime
	/* REDEFSTDFUNC */
	#define ctime(X) ctime64(X)
	#undef  ctime_r
	/* REDEFSTDFUNC */
	#define ctime_r(X,Y) ctime64_r(X,Y)
	#undef  gmtime
	#define gmtime(X) gmtime64(X)
	#undef  gmtime_r
	#define gmtime_r(X,Y) gmtime64_r(X,Y)
	#undef  localtime
	#define localtime(X) localtime64(X)
	#undef  localtime_r
	#define localtime_r(X,Y) localtime64_r(X,Y)
	#undef  mktime
	#define mktime(X) mktime64(X)
	#undef  time
	#define time(X) time64(X)
  #endif
#endif /* SAPonOS400 */


/*-----------------------------------------------------------------------------
 * sapuc.h - Functions that handle type char pointers:
 *          2. functions that return a type char pointer
 *             from the non-unicode world
 *----------------------------------------------------------------------------*/

#define asctimeU16_RETURN              SAP_UTF16*
#define asctimeU16_TPARAMS             (const struct tm *timeptr)
#define asctimeU16_PARAMS              (timeptr)
SAP_U16_PROTOTYPE_STDC_UC(asctime)
#define asctimeU(timeptr)              SAP_UNAME(asctime)(timeptr)

#define asctime_rU16_RETURN            SAP_UTF16*
#define asctime_rU16_TPARAMS           (const struct tm *timeptr, SAP_UTF16 * bufptr)
#define asctime_rU16_PARAMS            (timeptr, bufptr)
#ifdef SAPwithUNICODE
  SAP_U16_PROTOTYPE_UO(asctime_r)
#endif
#define asctime_rU(timeptr, bufptr)    SAP_UNAME(asctime_r)(timeptr, bufptr)

#define basenameU16_RETURN             SAP_UTF16*
#define basenameU16_TPARAMS            (SAP_UTF16 *path)
#define basenameU16_PARAMS             (path)
SAP_U16_PROTOTYPE_UO(basename)
#define basenameU(path)                SAP_UNAME(basename)(path)

#define ctimeU16_RETURN                SAP_UTF16*
#define ctimeU16_TPARAMS               (const time_t *timer)
#define ctimeU16_PARAMS                (timer)
SAP_U16_PROTOTYPE_STDC_UC(ctime)
#define ctimeU(timer)                  SAP_UNAME(ctime)(timer)

#define ctime_rU16_RETURN              SAP_UTF16*
#define ctime_rU16_TPARAMS             (const time_t *timer, SAP_UTF16 * bufptr)
#define ctime_rU16_PARAMS              (timer, bufptr)
#ifdef SAPwithUNICODE
  SAP_U16_PROTOTYPE_UO(ctime_r)
#endif
#define ctime_rU(timer, bufptr)        SAP_UNAME(ctime_r)(timer, bufptr)

#define dirnameU16_RETURN              SAP_UTF16*
#define dirnameU16_TPARAMS             (SAP_UTF16 *path)
#define dirnameU16_PARAMS              (path)
SAP_U16_PROTOTYPE_UO(dirname)
#define dirnameU(path)                 SAP_UNAME(dirname)(path)

#define ecvtU16_RETURN                 SAP_UTF16*
#define ecvtU16_TPARAMS                (double value, int ndig, int *dptr, int *sign)
#define ecvtU16_PARAMS                 (value, ndig, dptr, sign)
SAP_U16_PROTOTYPE(ecvt)
#if !defined(SAPwithUNICODE) && (defined(SAPonOS400) || defined(SAPonLIN))
  externC char *nlsui_ecvt(double value, int ndigit, int *decpt, int *sign);
  #define ecvtU(value, ndig, dptr, sign)  nlsui_ecvt(value, ndig, dptr, sign)
#else
  #define ecvtU(value, ndig, dptr, sign)  SAP_UNAME_(ecvt)(value, ndig, dptr, sign)
#endif

#define getcwdU16_RETURN               SAP_UTF16*
#define getcwdU16_TPARAMS              (SAP_UTF16 *wbuf, size_tU size)
#define getcwdU16_PARAMS               (wbuf, size)
SAP_U16_PROTOTYPE(getcwd)
#define getcwdU(buf, size)             SAP_UNAME_(getcwd)(buf, size)

#define mktempU16_RETURN               SAP_UTF16*
#define mktempU16_TPARAMS              (SAP_UTF16 *templ)
#define mktempU16_PARAMS               (templ)
SAP_U16_PROTOTYPE(mktemp)
#define mktempU(templ)                 SAP_UNAME_(mktemp)(templ)

#define setlocaleU16_RETURN            SAP_UTF16*
#define setlocaleU16_TPARAMS           (int category, const SAP_UC *w_inPtr)
#define setlocaleU16_PARAMS            (category, w_inPtr)
SAP_U16_PROTOTYPE(setlocale)
#if defined(SAPwithUNICODE) || !defined(SAPwithPASE400)
#define setlocaleU(cat, locale)        SAP_UNAME(setlocale)(cat, locale)
#else
#define setlocaleU(cat, locale)        setlocalePASE(cat, locale)
#endif

#define strerrorU16_RETURN             SAP_UTF16*
#define strerrorU16_TPARAMS            (int errnum)
#define strerrorU16_PARAMS             (errnum)
SAP_U16_PROTOTYPE_STDC(strerror)
#define strerrorU(errnum)              SAP_UNAME(strerror)(errnum)

#define tempnamU16_RETURN              SAP_UTF16*
#define tempnamU16_TPARAMS             (SAP_UTF16 *dir, SAP_UTF16 *prefix)
#define tempnamU16_PARAMS              (dir, prefix)
SAP_U16_PROTOTYPE(tempnam)
#define tempnamU(s, t)                 SAP_UNAME(tempnam)(s, t)

#define tmpnamU16_RETURN               SAP_UTF16*
#define tmpnamU16_TPARAMS              (SAP_UTF16 *wbuf)
#define tmpnamU16_PARAMS               (wbuf)
SAP_U16_PROTOTYPE(tmpnam)
#define tmpnamU(s)                     SAP_UNAME(tmpnam)(s)

#define ttynameU16_RETURN              SAP_UTF16*
#define ttynameU16_TPARAMS             (int filedes)
#define ttynameU16_PARAMS              (filedes)
SAP_U16_PROTOTYPE_UO(ttyname)
#define ttynameU(filedes)              SAP_UNAME(ttyname)(filedes)



#ifdef SAPonNT
  #define asctimeU16                   _wasctime
  #define basenameU16                  basename
  #define ctimeU16                     _wctime
  #define dirnameU16                   dirname
  #define getcwdU16                    _wgetcwd
  #define mktempU16                    _wmktemp
  #define setlocaleU16                 _wsetlocale
  #define tempnamU16                   _wtempnam
  #define tmpnamU16                    _wtmpnam
#endif



/*-----------------------------------------------------------------------
 * Continuous local time functionality (d023243, 12/2001)
 *
 * The C-Lib Functions
 * - localtime ( time_t -> tm )
 * - mktime    ( tm -> time_t )
 * - ctime     (= asctime(localtime()))
 * are dealing with local times that are discontinuous.
 * In time zones with daylight saving time (dst), the switch from summer
 * to winter time (dst -> non-dst) comes with one hour that is passed
 * through twice ("doubled hour"). One hour with dst, one without.
 * This functions solve the problem of the "doubled hour" by
 * retarding the time and making the time of two hours to only one hour.
 * See file .../src/flat/contloct.c
 *----------------------------------------------------------------------- */
#if defined(USE_CONT_LOCTIME)
  #if defined(CPP_USE_NEW_C_HEADERS)
    #include <ctime>
  #else
    #include <time.h>
  #endif
  externC DECL_EXP struct tm* CDCL_U localtime_cont(const time_t * t);
  externC struct tm* CDCL_U localtime_cont_r(const time_t * t, struct tm* res);
  externC time_t CDCL_U mktime_cont( struct tm * tm_in);
  externC SAP_CHAR* CDCL_U ctime_cont(const time_t* timer);
  externC SAP_CHAR* CDCL_U ctime_cont_r(const time_t* timer, SAP_CHAR* res);
  externC int IsDoubleInterval(time_t t);
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h - Functions that handle type char pointers:
 *
 *   3. I/O streams
 *
 *     including the printf and scanf function families
 *     and the fputc and fgetc function families
 *
 *     On a Unicode system, the ...U() which write to disk or read from disk
 *     convert between the Unicode format used in the memory and UTF-8.
 *     The ...R() functions read and write raw data without any conversion.
 *
 *     Some details of these functions are documented in flat/sapu16doc.htm
 *---------------------------------------------------------------------------*/
#define fgetcR(stream)                   fgetc(stream)
#define fgetcU16_RETURN                  int
#define fgetcU16_TPARAMS                 (FILE *stream)
#define fgetcU16_PARAMS                  (stream)
SAP_U16_PROTOTYPE(fgetc)
#define fgetcU(stream)                   SAP_UNAME(fgetc)(stream)

#define getcR(stream)                    getc(stream)
#define getcU(stream)                    NUC_UC(getc,fgetcU16)(stream)

#define ungetcR(c, stream)               ungetc(c, stream)

#define fputcR(rawdata, stream)          fputc(rawdata, stream)
#define fputcU16_RETURN                  int
#define fputcU16_TPARAMS                 (int wc,  FILE *stream)
#define fputcU16_PARAMS                  (wc,  stream)
SAP_U16_PROTOTYPE(fputc)
#define fputcU(c, stream)                SAP_UNAME(fputc)(c, stream)

#define putcR(rawdata, stream)           putc(rawdata, stream)
#define putcU(c, stream)                 NUC_UC(putc,fputcU16)(c, stream)

#define fwriteR(rawdata, s, n, stream)   fwrite(rawdata, s, n, stream)
externC DECL_EXP size_t fwriteU16( const SAP_UTF16 *, size_tU, size_t, FILE* stream);
#define fwriteU(buf, s, n, stream)       SAP_UNAME(fwrite)(buf, s, n, stream)

#define freadR( rawdata, s, n, stream)   fread( rawdata, s, n, stream)
#define freadU16_RETURN                  size_t
#define freadU16_TPARAMS                 (SAP_UTF16 * buf, size_tU s, size_t n, FILE * stream)
#define freadU16_PARAMS                  (buf, s, n, stream)
SAP_U16_PROTOTYPE(fread)
#define freadU(buf, s, n, stream)        SAP_UNAME(fread)(buf, s, n, stream)



/*************************************************************
 * ATTENTION:
 * Functions like fgetcU, fgetsU, freadU etc. convert in Unicode
 * case from UTF-8 to UTF-16.
 * If the input is not valid UTF-8, the functions insert a '#',
 * and set errno to EILSEQ. For a different error handling,
 * use fget_lineU, fget_strU, fget_longU, fget_intU.
 * See flat/sapu16doc.htm for details.
 *************************************************************/

#define fgetsR( s, n, stream )         fgets( (char*)(s), n, stream )
#define fgetsU16_RETURN                SAP_UTF16 *
#define fgetsU16_TPARAMS               (SAP_UTF16 *wcs, intU n, FILE *stream)
#define fgetsU16_PARAMS                (wcs, n, stream)
SAP_U16_PROTOTYPE(fgets)
#define fgetsU(s, n, stream)           SAP_UNAME(fgets)(s, n, stream)

#define getsR( s )                     /*SAPUNICODEOK_LIBFCT*/ gets( s )
#define getsU16_RETURN                 SAP_UTF16 *
#define getsU16_TPARAMS                (SAP_UTF16 *s)
#define getsU16_PARAMS                 (s)
SAP_U16_PROTOTYPE(gets)
#define getsU(s)                       SAP_UNAME(gets)(s)

#define fputsR( s, stream )            /*SAPUNICODEOK_LIBFCT*/ fputs( s, stream )
#define fputsU16_RETURN                intU
#define fputsU16_TPARAMS               (const SAP_UTF16 *wcs, FILE *stream)
#define fputsU16_PARAMS                (wcs, stream)
SAP_U16_PROTOTYPE(fputs)
#define fputsU(s, stream)              SAP_UNAME(fputs)(s, stream)

#define putsR( s )                     /*SAPUNICODEOK_LIBFCT*/ puts( s, stream )
#define putsU16_RETURN                 intU
#define putsU16_TPARAMS                (const SAP_UTF16 *wcs)
#define putsU16_PARAMS                 (wcs)
SAP_U16_PROTOTYPE(puts)
#define putsU(s)                       SAP_UNAME(puts)(s)

#define getcharU()                       getcU( stdin )
#define putcharU(c)                      putcU( c, stdout )


/* Here n counts the number of SAP_CHAR characters; buf may be of
 * type SAP_CHAR* . The usefulness may be quite limited;
 * consider using setvbufR instead.
 */
#define setvbufR(stream, buf, m, n )   setvbuf( stream, (char*)(buf), m, n )
#define setvbufU16(stream, buf, mod, n)  \
          setvbuf(stream, (char*)(buf), mod, (n)*SAP_UC_LN)
#define setvbufU(stream, buf, mod, n)    SAP_UNAME(setvbuf)(stream, buf, mod, n)


#ifdef SAPccQ
  BEGIN_NS_STD_C_HEADER
    #undef fgetsR
    externC void * fgetsR  ( void *s, intR n, FILE *f );
    #undef setvbufR
    externC int   setvbufR ( FILE *stream, void *buf, int m, size_tR n );
  END_NS_STD_C_HEADER
  #undef setvbufU
  extern int setvbufU( FILE *stream, SAP_CHAR *buf, int mod, size_tU n );
#endif


/* ungetcU not implemented. ungetwc on NT 4.0 cannot push back
 * more than two bytes, and moreover there is no UTF-8
 * locale (March 98). Similar problems on Linux.  */

#define printfU16_RETURN               int
#define printfU16_TPARAMS              (const SAP_UTF16 *format, ...)
#define printfU16_PARAMS               (format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(printf)      /* PRINTFLIKE1 */;
END_NS_STD_C_HEADER
#define printfU                        SAP_UNAME(printf)

#define fprintfU16_RETURN              int
#define fprintfU16_TPARAMS             (FILE* s, const SAP_UTF16 *format, ...)
#define fprintfU16_PARAMS              (s, format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(fprintf)     /* PRINTFLIKE2 */;
END_NS_STD_C_HEADER
#define fprintfU                       SAP_UNAME(fprintf)

#define sprintfU16_RETURN              intU
#define sprintfU16_TPARAMS             (SAP_UTF16* s, const SAP_UTF16 *format, ...)
#define sprintfU16_PARAMS              (s, format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(sprintf)     /* PRINTFLIKE2 */;
END_NS_STD_C_HEADER
#define sprintfU                       SAP_UNAME(sprintf)

#define snprintfU16_RETURN             intU
#define snprintfU16_TPARAMS            (SAP_UTF16* s, size_t n, const SAP_UTF16 *format, ...)
#define snprintfU16_PARAMS             (s, n, format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(snprintf)    /* PRINTFLIKE3 */;
END_NS_STD_C_HEADER

#if defined(va_start) || defined(SAPwithUNICODE)
  #define SAP_U16_PROTOTYPE_STDC_VALIST(name) SAP_U16_PROTOTYPE_STDC_HLP(name##U16)
#else
  #define SAP_U16_PROTOTYPE_STDC_VALIST(name)
#endif

#define vprintfU16_RETURN              int
#define vprintfU16_TPARAMS             (const SAP_UTF16 *format, va_list ap)
#define vprintfU16_PARAMS              (format, ap)
SAP_U16_PROTOTYPE_STDC_VALIST(vprintf)
#define vprintfU(p1, p2)               SAP_UNAME(vprintf)(p1, p2)

#define vfprintfU16_RETURN             int
#define vfprintfU16_TPARAMS            (FILE *s, const SAP_UTF16 *format, va_list ap)
#define vfprintfU16_PARAMS             (s, format, ap)
SAP_U16_PROTOTYPE_STDC_VALIST(vfprintf)
#define vfprintfU(p1, p2, p3)          SAP_UNAME(vfprintf)(p1, p2, p3)

#define vsprintfU16_RETURN             intU
#define vsprintfU16_TPARAMS            (SAP_UTF16 *s, const SAP_UTF16 *format, va_list ap)
#define vsprintfU16_PARAMS             (s, format, ap)
SAP_U16_PROTOTYPE_STDC_VALIST(vsprintf)
#define vsprintfU(p1, p2, p3)          SAP_UNAME(vsprintf)(p1, p2, p3)

externC int vsprintf_sRFB(char * s, size_tR s1max, const char *format, va_list ap );
#define vsprintf_sR                    vsprintf_sRFB
#define vsprintf_sU16_RETURN           intU
#define vsprintf_sU16_TPARAMS          (SAP_UTF16 *s, size_t n, const SAP_UTF16 *format, va_list ap)
#define vsprintf_sU16_PARAMS           (s, n, format, ap)
SAP_U16_PROTOTYPE_STDC_VALIST(vsprintf_s)
#define vsprintf_sU(p1, p2, p3, p4)    SAP_UNAME_UR(vsprintf_s)(p1, p2, p3, p4)

#define vsnprintfU16_RETURN            intU
#define vsnprintfU16_TPARAMS           (SAP_UTF16 *s, size_t n, const SAP_UTF16 *format, va_list ap)
#define vsnprintfU16_PARAMS            (s, n, format, ap)
SAP_U16_PROTOTYPE_STDC_VALIST(vsnprintf)

externC int vsnprintf_sRFB(char * s, size_tR s1max, const char *format, va_list ap );
#define vsnprintf_sR                   vsnprintf_sRFB
#define vsnprintf_sU16_RETURN          intU
#define vsnprintf_sU16_TPARAMS         (SAP_UTF16 *s, size_t n, const SAP_UTF16 *format, va_list ap)
#define vsnprintf_sU16_PARAMS          (s, n, format, ap)
SAP_U16_PROTOTYPE_STDC_VALIST(vsnprintf_s)
#define vsnprintf_sU(p1, p2, p3, p4)   SAP_UNAME_UR(vsnprintf_s)(p1, p2, p3, p4)

#define sscanfU16_RETURN               int
#define sscanfU16_TPARAMS              (const SAP_UTF16 *s, const SAP_UTF16 *format, ... )
#define sscanfU16_PARAMS               (s, format, rest_args )
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(sscanf)      /* SCANFLIKE2 */;
END_NS_STD_C_HEADER
#define sscanfU                        SAP_UNAME(sscanf)

/* deprecated */
#define scanfU16_RETURN                int
#define scanfU16_TPARAMS               (const SAP_UTF16 *format, ... )
#define scanfU16_PARAMS                (format, rest_args )
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(scanf)       /* SCANFLIKE1 */;
END_NS_STD_C_HEADER
#define scanfU                         SAP_UNAME(scanf)

/* deprecated */
#define fscanfU16_RETURN               int
#define fscanfU16_TPARAMS              (FILE *s, const SAP_UTF16 *format, ... )
#define fscanfU16_PARAMS               (s, format, rest_args )
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(fscanf)      /* SCANFLIKE2 */;
END_NS_STD_C_HEADER
#define fscanfU                        SAP_UNAME(fscanf)

#if defined(SAPonNT) && !defined(SAPccQ)
  #define sprintfU16                     swprintf
  #define vsprintfU16(p1, p2, p3)        vswprintf(p1, p2, p3)
  #define snprintfU16                    _snwprintf
  #define vsnprintfU16(p1, p2, p3, p4)   _vsnwprintf(p1, p2, p3, p4)
  #define sscanfU16                      swscanf
#endif


#if !defined(SAPwithUNICODE) && defined(SAPonOS400)
  externC intU as4_snprintfU
      ( SAP_UC* buffer, size_tU count, const SAP_UC* format, ... );
  #define snprintfU                    as4_snprintfU
  externC intU as4_vsnprintfU
      ( SAP_UC* buffer, size_tU count, const SAP_UC* format, va_list argptr );
  #if !defined(SAPwithCHAR_EBCDIC) || (__OS400_TGTVRM__==510)
  #define vsnprintfU(a,b,c,d)          as4_vsnprintfU(a,b,c,d)
  #if  defined(SAPwithCHAR_EBCDIC) && (__OS400_TGTVRM__==510)
  #define vsnprintf(a,b,c,d)           as4_vsnprintfU(a,b,c,d)
  #endif
  #else
  #define vsnprintfU(a,b,c,d)          vsnprintf(a,b,c,d)
  #endif
#else
  #define snprintfU                    SAP_UNAME_(snprintf)
  #define vsnprintfU(p1, p2, p3, p4)   SAP_UNAME_(vsnprintf)(p1, p2, p3, p4)
#endif

#if defined SAPonOS400  && !defined(SAPwithCHAR_EBCDIC)
  externC int as4_snprintfA
      ( char* buffer, size_tR count, const char* format, ... );
  externC int as4_vsnprintfA
      ( char* buffer, size_tR count, const char* format, va_list argptr );
  #define snprintf            as4_snprintfA
  #define vsnprintf(a,b,c,d)  as4_vsnprintfA(a,b,c,d)
#endif

/*-----------------------------------------------------------------------------
 * sapuc.h - Functions that handle type char pointers:
 *   3a. Functions to avoid fscanf
 *       See flat/sapu16doc.htm for details.
 *----------------------------------------------------------------------------*/

/* Prototypes for Unicode and non-Unicode */
externC DECL_EXP int fget_strR( char *s, int n, FILE *stream, SAP_UC repl_char );
#define fget_strU16_RETURN               int
#define fget_strU16_TPARAMS              (SAP_UTF16 *s, int n, FILE *stream, \
                                          SAP_UTF16 repl_char)
#define fget_strU16_PARAMS               (s, n, stream, repl_char)
SAP_U16_PROTOTYPE(fget_str)
#define fget_strU(s, n, stream, r)       SAP_UNAME_UR(fget_str)(s, n, stream, r)

externC DECL_EXP int fget_lineR( char *s, int n, FILE *stream, SAP_UC repl_char );
#define fget_lineU16_RETURN              int
#define fget_lineU16_TPARAMS             (SAP_UTF16 *s, int n, FILE *stream, \
                                          SAP_UTF16 repl_char)
#define fget_lineU16_PARAMS              (s, n, stream, repl_char)
SAP_U16_PROTOTYPE(fget_line)
#define fget_lineU(s, n, stream, r)      SAP_UNAME_UR(fget_line)(s, n, stream, r)

externC DECL_EXP int fget_longR( long int* ptr, FILE *stream );
#define fget_longU16_RETURN              int
#define fget_longU16_TPARAMS             (long int* ptr, FILE *stream)
#define fget_longU16_PARAMS              (ptr, stream)
SAP_U16_PROTOTYPE(fget_long)
#define fget_longU(p, stream)            SAP_UNAME_UR(fget_long)(p, stream)

externC DECL_EXP int fget_intR( int* ptr, FILE *stream );
#define fget_intU16_RETURN               int
#define fget_intU16_TPARAMS              (int* ptr, FILE *stream)
#define fget_intU16_PARAMS               (ptr, stream)
SAP_U16_PROTOTYPE(fget_int)
#define fget_intU(p, stream)             SAP_UNAME_UR(fget_int)(p, stream)


/*-----------------------------------------------------------------------------
 * sapuc.h - Functions that handle type char pointers:
 *         4. exec family
 *----------------------------------------------------------------------------*/

#define execlU16_RETURN                  int
#define execlU16_TPARAMS                 (const SAP_UTF16 *path, const SAP_UTF16 *arg, ... )
#define execlU16_PARAMS                  (path, arg, rest_args )
SAP_U16_PROTOTYPE_UX(execl)
#define execlU                           SAP_UNAME(execl)

#define execleU16_RETURN                 int
#define execleU16_TPARAMS                (const SAP_UTF16 *path, const SAP_UTF16 *arg, ... )
#define execleU16_PARAMS                 (path, arg, rest_args )
SAP_U16_PROTOTYPE_UX(execle)
#define execleU                          SAP_UNAME(execle)

#define execlpU16_RETURN                 int
#define execlpU16_TPARAMS                (const SAP_UTF16 *file, const SAP_UTF16 *arg, ... )
#define execlpU16_PARAMS                 (file, arg, rest_args )
SAP_U16_PROTOTYPE_UX(execlp)
#define execlpU                          SAP_UNAME(execlp)

#define execvU16_RETURN                  int
#define execvU16_TPARAMS                 (const SAP_UTF16 *path, SAP_UTF16* const argv[])
#define execvU16_PARAMS                  (path, argv)
SAP_U16_PROTOTYPE_UX(execv)
#define execvU(p1, p2)                   SAP_UNAME(execv)(p1, p2)

#define execveU16_RETURN                 int
#define execveU16_TPARAMS                (const SAP_UTF16 *path, SAP_UTF16* const argv[], \
                                          SAP_UTF16* const wenv[] )
#define execveU16_PARAMS                 (path, argv, wenv )
SAP_U16_PROTOTYPE_UX(execve)
#define execveU(p1, p2, p3)              SAP_UNAME(execve)(p1, p2, p3)

#define execvpU16_RETURN                 int
#define execvpU16_TPARAMS                (const SAP_UTF16 *path, SAP_UTF16* const argv[])
#define execvpU16_PARAMS                 (path, argv)
SAP_U16_PROTOTYPE_UX(execvp)
#if !defined(SAPwithPASE400)
#define execvpU(p1, p2)                  SAP_UNAME(execvp)(p1, p2)
#else
#define execvpU(p1, p2)                  (isQSYSFileNameU(p1) ? as4_execvp(p1, p2) : SAP_UNAME(execvp)(p1, p2))
externC int as4_execvp( const SAP_UC *path, SAP_UC* const argv[]);
externC int isQSYSFileNameU ( const SAP_UC* pszIFSPath );
#endif

#if defined(SAPonNT)
  #define execlU16                       _wexecl
  #define execleU16                      _wexecle
  #define execlpU16                      _wexeclp
  #define execvU16                       _wexecv
  #define execveU16                      _wexecve
  #define execvpU16                      _wexecvp
#endif


#if defined(SAPonOS390) || defined(SAPonOS400)
  #if defined(SAPwithUNICODE)
    externC int spawnU16( const SAP_UTF16 *path,
                          const int     fd_count,
                          const int     fd_map[],
                          const struct  inheritance *inherit,
                          SAP_UTF16* const argv[],
                          SAP_UTF16* const wenv[]);
    #define spawnU(p1,p2,p3,p4,p5,p6)      SAP_UNAME(spawn)(p1,p2,p3,p4,p5,p6)
  #else
    #ifdef SAPonOS400
      #define spawnU(p1,p2,p3,p4,p5,p6)      SAP_UNAME(spawn)(p1,p2,p3,p4,p5,p6)
    #else
      #define spawnU(p1,p2,p3,p4,p5,p6)      SAP_UNAME(spawn)(p1,p2,p3,p4,(const char **)(p5),(const char **)(p6))
    #endif
  #endif
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h -  Environment handling and main
 *
 * Usage of the mainU() and main3U() macros:
 * The source code looks like this:
 *
 *     int mainU (int argc, SAP_UC *argv[ ] ) { .... }
 *
 *     int main3U (int argc, SAP_UC *argv[ ], SAP_UC *envp[ ] ) { .... }
 *
 * For a documentation of the following macros and an example of
 * their use, see the docu in flat/nlsuidoc.htm:
 *    environU, DECLAREenvironU, GETenvironU, FREEenvironU
 *----------------------------------------------------------------------------*/

#define getenvU16_RETURN               SAP_UTF16*
#define getenvU16_TPARAMS              (const SAP_UTF16 *wname)
#define getenvU16_PARAMS               (wname)
SAP_U16_PROTOTYPE_STDC(getenv)
#define getenvU(name)                  SAP_UNAME(getenv)(name)

#define putenvU16_RETURN               int
#define putenvU16_TPARAMS              (const SAP_UTF16 *wcs)
#define putenvU16_PARAMS               (wcs)
SAP_U16_PROTOTYPE(putenv)
#define putenvU(s)                     SAP_UNAME_(putenv)(s)
#define _putenvU(s)                    putenvU(s)

#ifdef SAPonNT
  #define getenvU16                    _wgetenv
  #define putenvU16                    _wputenv
#endif

#define environU                       SAP_UNAME_UR(environ)
#define DECLAREenvironU                SAP_UNAME_UR(DECLAREenviron)
#define GETenvironU                    SAP_UNAME_UR(GETenviron)
#define FREEenvironU                   SAP_UNAME_UR(FREEenviron)

#if defined(SAPonNT)
  #define environU16                   _wenviron
  #define DECLAREenvironU16            short sapu16cu_env_unused_var
                                       /* dummy variable for syntax reasons;
                                        * _wenviron is a macro in stdlib.h */
  #define GETenvironU16                /*CCQ_NO_EFFECT_OK*/_wenviron
  #define FREEenvironU16               /*CCQ_NO_EFFECT_OK*/(1)
#else
  #define environU16                   nlsui_environ
  #define DECLAREenvironU16            SAP_UTF16 **nlsui_environ_i, **nlsui_environ
  #define GETenvironU16                (nlsui_environ = nlsui_environ_i = nlsui_getenvironU())
  #define FREEenvironU16               nlsui_freeenvironU(nlsui_environ_i)

    /* The following prototypes are for internal use only.
     * (Don't use the functions directly.) */
    externC SAP_UTF16 **               nlsui_getenvironU  ( void );
    externC int                        nlsui_freeenvironU ( SAP_UTF16 ** );
#endif

#if defined(SAPonOS400) && defined(SAPwithCHAR_ASCII)
  #define environR						o4_environ_a
#else
  #define environR                      environ
#endif
#ifdef SAPonNT
  #define DECLAREenvironR               short sapu16cr_env_unused_var
                                        /* dummy variable for syntax reasons;
                                         * _environ is a macro in stdlib.h */
#else
  #if defined(SAPonOS400) && defined(SAPwithCHAR_ASCII)
  #define DECLAREenvironR               extern char ** o4_environ_a
  #else
  #define DECLAREenvironR               extern char ** environ
  #endif
#endif
#ifdef SAPonOS400
  #if defined(SAPwithCHAR_ASCII)
    # define GETenvironR				((o4_convert_environ_a() == 0) ? o4_environ_a : NULL)
  #else
    # define GETenvironR                ((Qp0zInitEnv() == 0) ? environ : NULL)
  #endif
#else
  # define GETenvironR                  /*CCQ_NO_EFFECT_OK*/environ
#endif
#if defined(SAPonOS400) && defined(SAPwithCHAR_ASCII)
  #define FREEenvironR                  o4_free_environ_a()
#else
  #define FREEenvironR                  /*CCQ_NO_EFFECT_OK*/(1)
#endif

/* hook to allow initial private code before NLSUI_INIT_HOOK is called
   if the hook is definied its function is executed as the very first one.
   In order to use the same mechanism for non UC programs the simple
   #define mainU main had to be eliminated
*/
#ifdef MAINU_INIT_HOOK
  #define MAINU_INIT_HOOK_MAYBE(ARGC, ARGV) MAINU_INIT_HOOK(ARGC, ARGV);
#else
  #define MAINU_INIT_HOOK_MAYBE(ARGC, ARGV)
#endif

/* declare nlsui_main before calling it */

externC int  nlsui_main       ( int argc, SAP_UC *argv[] );
externC int  nlsui_main3      ( int argc, SAP_UC *argv[],
                                          SAP_UC *envp[] );
externC DECL_EXP void CDCL_U nlsui_initialize( void );

#if !defined(SAPUCX_H)
externC DECL_EXP void CDCL_U nlsui_store_cmdline( int argc, SAP_UC *argv[] );
 #define NLSUI_STORE_CMDLINE( argc, argv ) nlsui_store_cmdline( argc, argv );
#else 
 #define NLSUI_STORE_CMDLINE( argc, argv )
#endif

#if !defined(SAPUCX_H)
externC DECL_EXP void CDCL_U nlsui_set7bitUnicode ( void );
#endif

#if !defined( SAPwithNLSUI_INITIALIZE )

  #define mainU                                                \
    main( int argc, char *argv[ ] )                            \
    {                                                          \
      MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
      return nlsui_main( argc, argv );                         \
    }                                                          \
    int nlsui_main /* (...) */

  #define main3U                                               \
    main( int argc, char *argv[ ], char *envp[ ] )             \
    {                                                          \
      MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
      return nlsui_main3( argc, argv, envp );                  \
    }                                                          \
    int nlsui_main3 /* (...) */

#else  /* Now SAPwithUNICODE or activated ICU functionality in non-Unicode programs */

  /* hook to allow setting of environment variables before loading i18n libs
     if NLSUI_INIT_HOOK exists it is called with ARGC and ARGV (type SAP_UC**)
     after argument conversion to SAP_UC and before loading of any shared lib
     no U function may be used within NLSUI_INIT_HOOK
     usage of UcnToB7n to convert command line parameters to Non-Unicode is ok
  */
  #ifdef NLSUI_INIT_HOOK
    #define NLSUI_INIT_HOOK_MAYBE(ARGC,ARGV)    NLSUI_INIT_HOOK(ARGC,ARGV);
  #else
    #define NLSUI_INIT_HOOK_MAYBE(ARGC,ARGV)
  #endif

  #ifdef SAPwith7BIT_UNICODE
    #define NLSUI_SET_7BIT_MAYBE nlsui_set7bitUnicode();
  #else
    #define NLSUI_SET_7BIT_MAYBE
  #endif


  #ifndef SAPwithUNICODE

    #define mainU                                                \
      main( int argc, char *argv[ ] )                            \
      {                                                          \
        MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_SET_7BIT_MAYBE                                     \
        NLSUI_STORE_CMDLINE(argc, argv)                          \
        nlsui_initialize();                                      \
        return nlsui_main( argc, argv );                         \
      }                                                          \
      int nlsui_main /* (...) */

    #define main3U                                               \
      main( int argc, char *argv[ ], char *envp[ ] )             \
      {                                                          \
        MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_SET_7BIT_MAYBE                                     \
        NLSUI_STORE_CMDLINE(argc, argv)                          \
        nlsui_initialize();                                      \
        return nlsui_main3( argc, argv, envp );                  \
      }                                                          \
      int nlsui_main3 /* (...) */

  #else /* now SAPwithUNICODE */

   #ifdef SAPonNT


    #define mainU                                                \
      wmain( int argc, wchar_t *argv[ ] )                        \
      {                                                          \
        MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_SET_7BIT_MAYBE                                     \
        NLSUI_STORE_CMDLINE(argc, argv)                          \
        nlsui_initialize();                                      \
        return nlsui_main( argc, argv );                         \
      }                                                          \
      int nlsui_main /* (...) */

    #define main3U                                               \
      wmain( int argc, wchar_t *argv[ ], wchar_t *envp[ ] )      \
      {                                                          \
        MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_INIT_HOOK_MAYBE(argc, argv)                        \
        NLSUI_SET_7BIT_MAYBE                                     \
        NLSUI_STORE_CMDLINE(argc, argv)                          \
        nlsui_initialize();                                      \
        return nlsui_main3( argc, argv, envp );                  \
      }                                                          \
      int nlsui_main3 /* (...) */


   #else /* other platforms than NT */

    #define mainU                                                \
      main( int argc, char *argv[ ] )                            \
      {                                                          \
        SAP_UC **w_argv;                                         \
        MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
        w_argv = nlsui_alloc_wcsar( argc, argv );                \
        NLSUI_INIT_HOOK_MAYBE(argc, w_argv)                      \
        NLSUI_SET_7BIT_MAYBE                                     \
        NLSUI_STORE_CMDLINE(argc, w_argv)                        \
        nlsui_initialize();                                      \
        return nlsui_main( argc, w_argv );                       \
      }                                                          \
      int nlsui_main /* (...) */

    #define main3U                                               \
      main( int argc, char *argv[ ], char *envp[ ] )             \
      {                                                          \
        SAP_UC **w_argv, **w_envp;                               \
        MAINU_INIT_HOOK_MAYBE(argc, argv)                        \
        w_argv = nlsui_alloc_wcsar( argc, argv );                \
        w_envp = nlsui_alloc_env( envp );                        \
        NLSUI_INIT_HOOK_MAYBE(argc, w_argv)                      \
        NLSUI_SET_7BIT_MAYBE                                     \
        NLSUI_STORE_CMDLINE(argc, w_argv)                        \
        nlsui_initialize();                                      \
        return nlsui_main3( argc, w_argv, w_envp );              \
      }                                                          \
      int nlsui_main3 /* (...) */

    externC DECL_EXP SAP_UC ** nlsui_alloc_wcsar ( int argc,  char *argv[]);
    externC int       nlsui_wcsar2mbsar  ( int cnt,   SAP_UC *wp[],
                                           char *p[], int plen[] );
    externC SAP_UC ** nlsui_alloc_env    ( char **envp );
    #ifdef SAPonOS400
      extern int     nlsui_o4_main       ( int o4_argc, SAP_UC *w_argv[] );
    #endif /* SAPonOS400 */

   #endif /* different platforms */

  #endif /* SAPwithUNICODE */

#endif /* SAPwithUNICODE or not */

/* function to load ICU without using the mainU() macro */
#if defined(SAPwithICU) && !defined(SAPUCX_H)
externC SAPRETURN CDCL_U loadIcu( SAP_BOOL doReturn );
#endif

/* function to enhance the ICU search path, to be used with MAINU_INIT_HOOK */
#if !defined(SAPUCX_H)
externC void CDCL_U nlsui_addIcuSearchPath( char *path );
#endif

/* ccQ complains about main expansion with char, so let mainU, main3U be
 * simple functions
 */
#ifdef SAPccQ
  /* extern int mainU   ( int argc, SAP_UC **argv ); */
  /* extern int main3U  ( int argc, SAP_UC **argv, SAP_UC **envptr ); */
  #undef mainU
  #undef main3U
#endif


/*---------------------------------------------------------------------
 * sapuc.h  -  NLS specific functions (multibyte functions)
 *
 *  MB_CUR_MAX was used to distinguish between multibyte-enabled code
 *  and single byte code. In the Unicode case, we have a similar
 *  distinction between UTF-16 enabled code and UCS2 code. There are
 *  three macros that allow to distinguish three possible cases:
 *  1. MB_CUR_MAX_U
 *     Code that is valid for both multibyte and UTF-16.
 *  2. MB_CUR_MAX_NUC
 *     Code that is valid for multibyte but would be unnecessarily
 *     complicated for UTF-16.
 *  3. MB_CUR_MAX_UC
 *     Code that is valid for UTF-16 but would not be correct for
 *     multibyte.
 *  By default, MB_CUR_MAX should be replaced by MB_CUR_MAX_NUC.
 *  As long as MB_CUR_MAX is not yet replaced in all cases, we must
 *  #define it to be (1) in the Unicode case n order to avoid running
 *  into the multibyte code.
 *
 *  mblenU() can be used in all three cases to identify sequences
 *  of SAP_CHARs that form one character (either a multibyte character
 *  or a surrogate pair).
 *
 *  Conversions between multibyte and wide characters are reduced
 *  to a memcpy in the Unicode case.
 *--------------------------------------------------------------------*/

  /* Do a #undef mblenU if you need a real function.  */
  int mblenU( const SAP_UC *mbptr, size_tU units );

#if !defined(SAPwithUNICODE)

  #define MB_CUR_MAX_U                    MB_CUR_MAX
  #define MB_CUR_MAX_NUC                  MB_CUR_MAX
  #define MB_CUR_MAX_UC                   (1)
  #define mblenU(mbptr, nbytes)           mblen(mbptr, nbytes)

#else /* SAPwithUNICODE */

  #ifdef NO_STDLIB_H
    /* see saptypeb.h. We need stdlib.h or cstdlib because it may #define
     * MB_CUR_MAX again
     */
    #error "stdlib.h must be included before sapuc.h"
  #endif

  #ifndef SAPUCX_H /* not in a customer's RFC SDK program */
    #undef MB_CUR_MAX
    #define MB_CUR_MAX                  (1)
  #endif
  #define MB_CUR_MAX_U                  (2)
  #define MB_CUR_MAX_NUC                (1)
  #define MB_CUR_MAX_UC                 (2)

  /* Remember important constants for UTF-16:
   *
   * The first 16-bit code value of surrogate characters is in the
   * range from 0xD800UL thru 0xDBFFUL.
   * The second 16-bit code value of surrogate characters is in the
   * range from 0xDC00UL thru 0xDFFFUL.
   */

  #define mblenU(mbptr, units)                                       \
  ( ( ((const SAP_UC*)(mbptr)) == (SAP_UC*)0 )              \
    ? /* no valid input */                               0  \
    : ( (     ( *((const SAP_UC*)(mbptr)) < 0xD800UL )      \
           || ( *((const SAP_UC*)(mbptr)) > 0xDFFFUL ) )    \
        ? /* normal char [U-0000,U-D7FF],[U-E000,U-FFFD] */       1  \
        : ( ( units > (size_tU)1 )        \
            ? ((   *((const SAP_UC*)(mbptr)) <= 0xDBFFUL )           \
               ? ( (    ((const SAP_UC*)(mbptr))[1] >= 0xDC00UL      \
                     && ((const SAP_UC*)(mbptr))[1] <= 0xDFFFUL )    \
                   ? /* surrogate char     */                     2  \
                   : /* 2nd half not valid */                    -1  \
                 )                        \
               : /* 1st half missing */                          -1  \
              )                           \
            :    /* 2nd half missing */                          -1  \
          )                               \
      )                                   \
  )

  /* For performance reasons I do not test for callers
   * giving me 0 units. I hope it will never happen.
   */

#endif  /* SAPwithUNICODE */


#ifndef SAPwithUNICODE
  #define mbstowcsU(dest, source, len)   mbstowcs(dest, source, len)
  #define wcstombsU(dest, source, len)   wcstombs(dest, source, len)
  #define mbtowcU(wcptr, mbptr, nbytes)  mbtowc(wcptr, mbptr, nbytes)
  #define wctombU(mbptr, wc)             wctomb(mbptr, wc)

#else   /* Now SAPwithUNICODE */
  #define mbstowcsU(dest, source, noch)  wcstowcs(dest, source, noch)
  #define wcstombsU(dest, source, noch)  wcstowcs(dest, source, noch)
  externC size_tU CDCL_U wcstowcs(SAP_UC *dest, const SAP_UC *source, size_tU noch);
  #define mbtowcU(wcptr, mbptr, nbytes)  ( (wcptr)!=NULL && (mbptr)!=NULL ? \
                                           ( *(wcptr)=*(mbptr), (size_t)1 ) : \
                                           (size_t)0  )
  #define wctombU(mbptr, wc)             ( (mbptr)!=NULL ? \
                                           ( *(mbptr)=(wc), (size_t)1) : \
                                           (size_t)0  )

#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -  structures which contain elements of type char
 *             and functions which use these stuctures
 *
 * the following defintions should only be present if _POSIX_SOURCE is defined
 *----------------------------------------------------------------------------*/
/*-----------------------------------------------------------------------------
 * sapuc.h  - Definition of some preprocessor constants
 *
 *  Other similar constants are defined in nlsui1.c and nlsui2.c.
 *  If used as string length, the terminating zero is included in this length.
 *  Typical file name buffer declaration b[MAX_PATH_LN], for b as string.
 *----------------------------------------------------------------------------*/
#define MAX_ALIASES           64       /* hostname aliases (struct hostentU)  */
#define MAX_ADDRESSES         64       /* hostname adresses (struct hostentU) */

#if defined(SAPonNT)
 #define MAX_PATH_LN     _MAX_PATH
#elif defined(SAPonOS400)
 #define MAX_PATH_LN     _QP0L_DIR_NAME  /* see qsyuinc/h.dirent              */
 #define SAP_SYS_NMLN    32              /* see "o4port.h"                    */
#elif !defined(PATH_MAX)                /* PATH_MAX <limits.h> not present XXX? */
 #define MAX_PATH_LN     1024
 #define SAP_SYS_NMLN    256
#else
 #define MAX_PATH_LN     (PATH_MAX+1)    /* <sys/limits.h>, no terminating 0  */
 #define SAP_SYS_NMLN    256
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  - struct utsname and function uname()
 *----------------------------------------------------------------------------*/
#ifndef SAPwithUNICODE

  #define utsnameU              utsname
  #define unameU(name_ptr)      uname(name_ptr)

#else  /* Now SAPwithUNICODE */

  #ifdef SAPonNT
    #define utsnameU              utsname
    #define unameU(name_ptr)      uname(name_ptr)
  #else
    struct utsnameU {
      SAP_UC sysname[SAP_SYS_NMLN];
      SAP_UC nodename[SAP_SYS_NMLN];
      SAP_UC release[SAP_SYS_NMLN];
      SAP_UC version[SAP_SYS_NMLN];
      SAP_UC machine[SAP_SYS_NMLN];
    };
    externC int unameU( struct utsnameU  *name );
  #endif

#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  - struct dirent and functions opendir, readdir
 *----------------------------------------------------------------------------*/

#ifdef SAPonNT

  #define opendirU(path)        opendir(path)
  #define direntU               dirent
  #define readdirU(dirp)        readdir(dirp)

#elif (!defined (SAPonHP_UX)) || defined (_INCLUDE_POSIX_SOURCE)

  #define opendirU16_RETURN              DIR*
  #define opendirU16_TPARAMS             (const SAP_UTF16 *path)
  #define opendirU16_PARAMS              (path)
  SAP_U16_PROTOTYPE_UC(opendir)
  #define opendirU(path)                 SAP_UNAME(opendir)(path)

#if defined(SAPwithUNICODE) || defined(SAPUC_H_WITH_direntU)
  struct direntU16 {
    ino_t       d_ino;
  #if defined(SAPonSUN) || defined(SAPonLIN)
    /* there is no namelen entry */
  #else
    SAP_USHORT  d_namlen;
  #endif
    SAP_UTF16   d_name[MAX_PATH_LN];
  };
#endif

  #define direntU                        SAP_UNAME(dirent)

  #define readdirU16_RETURN              struct direntU16*
  #define readdirU16_TPARAMS             (DIR *dirp)
  #define readdirU16_PARAMS              (dirp)
#ifdef SAPwithUNICODE
  SAP_U16_PROTOTYPE(readdir)
#endif
  #define readdirU(dirp)                 SAP_UNAME(readdir)(dirp)

  #ifdef SAPonUNIX
    #define readdir_rU16_RETURN          int
    #define readdir_rU16_TPARAMS         (DIR * dirp, struct direntU16 * entry,\
                                         struct direntU16 ** result)
    #define readdir_rU16_PARAMS          (dirp,entry,result)
#ifdef SAPwithUNICODE
    SAP_U16_PROTOTYPE(readdir_r)
#endif
    #define readdir_rU(dirp,entry,result) \
                                         SAP_UNAME(readdir_r)(dirp,entry,result)
  #endif
#endif



/*-----------------------------------------------------------------------------
 * sapuc.h  - struct passwd and functions getpw...()
 *            For the Unicode case, uid_t and gid_t are replaced by
 *            SAP_UINT. Therefore it is not necessary to include
 *            <sys/types.h> here.
 *----------------------------------------------------------------------------*/

struct passwdU16 {
    SAP_UTF16 *pw_name;
 #ifndef SAPonOS400
    SAP_UTF16 *pw_passwd;
 #endif
    SAP_UINT pw_uid;
    SAP_UINT pw_gid;
 #ifndef SAPonOS400
    SAP_UTF16 *pw_gecos;
 #endif
    SAP_UTF16 *pw_dir;
    SAP_UTF16 *pw_shell;
};
#define passwdU                 SAP_UNAME(passwd)

#define AS4_EXT_PTR
#if defined(SAPccQ) && defined(SAPonOS400)
#define __ptr128
#endif

#define getpwuidU16_RETURN      struct passwdU16 * AS4_EXT_PTR
#define getpwuidU16_TPARAMS     (SAP_UINT uid)
#define getpwuidU16_PARAMS      (uid)
SAP_U16_PROTOTYPE_UO(getpwuid)
#define getpwuidU(uid)          SAP_UNAME(getpwuid)(uid)

#define getpwnamU16_RETURN      struct passwdU16 * AS4_EXT_PTR
#define getpwnamU16_TPARAMS     (const SAP_UTF16 *name)
#define getpwnamU16_PARAMS      (name)
SAP_U16_PROTOTYPE_UO(getpwnam)
#define getpwnamU(name)         SAP_UNAME(getpwnam)(name)



/*-----------------------------------------------------------------------------
 * sapuc.h  - struct hostent and struct servent
 *            and the functions
 *            gethostent(), gethostbyname(), gethostbyaddr(),
 *            getservbyname(), getservbyport(),
 *            gethostbyname_r(), gethostbyaddr_r(),
 *            getservbyname_r(), getservbyport_r(),
 *            rexecU()
 *----------------------------------------------------------------------------*/

struct hostentU16 {
    SAP_UTF16  * h_name;                    /* official name of host         */
    SAP_UTF16  * h_aliases[MAX_ALIASES];    /* alias list                    */
    SAP_INT      h_addrtype;                /* host address type             */
    SAP_INT      h_length;                  /* length of address in bytes    */
    SAP_RAW *    h_addr_list[MAX_ADDRESSES];/* list of addr. from name server*/
    #define      h_addr  h_addr_list[0]     /* address, for backw. compatib. */
};
#define hostentU                        SAP_UNAME(hostent)

struct serventU16 {
    SAP_UTF16   * s_name;                  /* official service name */
    SAP_UTF16   * s_aliases[MAX_ALIASES];  /* alias list            */
    SAP_INT       s_port;                  /* port #                */
    SAP_UTF16   * s_proto;                 /* protocol to use       */
};
#define serventU                        SAP_UNAME(servent)

#define gethostentU16_RETURN            struct hostentU16 *
#define gethostentU16_TPARAMS           (void)
#define gethostentU16_PARAMS            ()
SAP_U16_PROTOTYPE(gethostent)
#define gethostentU()                   SAP_UNAME(gethostent)()

#define gethostbyaddrU16_RETURN         struct hostentU16 *
#define gethostbyaddrU16_TPARAMS        (const void *addr, int len, int type)
#define gethostbyaddrU16_PARAMS         (addr, len, type)
SAP_U16_PROTOTYPE(gethostbyaddr)
#define gethostbyaddrU(addr,len,type)   SAP_UNAME(gethostbyaddr)(addr,len,type)

#define gethostbynameU16_RETURN         struct hostentU16 *
#define gethostbynameU16_TPARAMS        (const SAP_UTF16 *name)
#define gethostbynameU16_PARAMS         (name)
SAP_U16_PROTOTYPE(gethostbyname)
#define gethostbynameU(name)            SAP_UNAME(gethostbyname)(name)

#define getservbynameU16_RETURN         struct serventU16 *
#define getservbynameU16_TPARAMS        (const SAP_UTF16 *name, const SAP_UTF16 *proto)
#define getservbynameU16_PARAMS         (name, proto)
SAP_U16_PROTOTYPE(getservbyname)
#define getservbynameU(name, proto)     SAP_UNAME(getservbyname)(name, proto)

#define getservbyportU16_RETURN         struct serventU16 *
#define getservbyportU16_TPARAMS        (int port, const SAP_UTF16 *proto)
#define getservbyportU16_PARAMS         (port, proto)
SAP_U16_PROTOTYPE(getservbyport)
#define getservbyportU(port, proto)     SAP_UNAME(getservbyport)(port, proto)

#if defined(SAPonHP_UX) || defined(SAPonSUN) || defined(SAPonAIX) || \
    defined(SAPonOSF1)  || defined(SAPonLIN) || defined(SAPonOS390)

  #define rexecU16_RETURN                int
  #define rexecU16_TPARAMS               (SAP_UC ** host, int port, const SAP_UC * name, \
                                          const SAP_UC * pass, const SAP_UC * cmd, int * fd2p)
  #define rexecU16_PARAMS                (host, port, name, pass, cmd, fd2p )
  SAP_U16_PROTOTYPE(rexec)
  #define rexecU(host, port, name, pass, cmd, fd2p)  \
                                         SAP_UNAME(rexec)(host, port, name, pass, cmd, fd2p)
#endif



/*-----------------------------------------------------------------------------
 * sapuc.h  -  struct group and function getgrgid()
 *----------------------------------------------------------------------------*/

#if defined(SAPonUNIX) || defined(SAPonOS400)
  struct groupU16 {
      SAP_UTF16     *gr_name;
    #ifndef SAPonOS400
      SAP_UTF16     *gr_passwd;
    #endif
      unsigned long  gr_gid;
      SAP_UTF16    **gr_mem;
  };
  #define groupU                       SAP_UNAME(group)

  #define getgrgidU16_RETURN           struct groupU16* AS4_EXT_PTR
  #define getgrgidU16_TPARAMS          (unsigned long gid)
  #define getgrgidU16_PARAMS           (gid)
  SAP_U16_PROTOTYPE(getgrgid)
  #define getgrgidU(gid)               SAP_UNAME(getgrgid)(gid)

  #ifdef SAPonOS400
    #define getgrnamU16_RETURN         struct groupU16* AS4_EXT_PTR
    #define getgrnamU16_TPARAMS        (SAP_UTF16* grname)
    #define getgrnamU16_PARAMS         (grname)
    SAP_U16_PROTOTYPE(getgrnam)
    #define getgrnamU(grname)          SAP_UNAME(getgrnam)(grname)
  #endif
#endif



/*-----------------------------------------------------------------------------
 * sapuc.h  -  function getpass
 *----------------------------------------------------------------------------*/

#ifdef SAPonNT
  #define getpassU( prompt )  getpass( prompt )
#else
  #define getpassU16_RETURN            SAP_UTF16*
  #define getpassU16_TPARAMS           (const SAP_UTF16* prompt)
  #define getpassU16_PARAMS            (prompt)
  SAP_U16_PROTOTYPE(getpass)
  #define getpassU(prompt)             SAP_UNAME(getpass)(prompt)
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -  statvfs()
 *----------------------------------------------------------------------------*/

#ifndef SAPonNT
  externC int statvfsU;
  #define statvfsU16_RETURN            int
  #define statvfsU16_TPARAMS           (const SAP_UC * path, struct statvfs * buf)
  #define statvfsU16_PARAMS            (path,buf)
  struct statvfs;
  SAP_U16_PROTOTYPE(statvfs)
  #define statvfsU(path,buf)          SAP_UNAME(statvfs)(path,buf)
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -  xdr_string()
 *----------------------------------------------------------------------------*/

#if defined(SAPonAIX)   &&   defined(_RPC_XDR_H)        \
 || defined(SAPonSUN)   &&   defined(_RPC_XDR_H)        \
 || defined(SAPonHP_UX) && ( defined(_RPC_XDR_INCLUDED) \
                          || defined(_RPC_XDR_H) )      \
 || defined(SAPonOSF1)  &&   defined(_rpc_xdr_h)        \
 || defined(SAPonOS390) &&   defined(__XDR_HEADER__)    \
 || defined(SAPonLIN)   &&   defined(_RPC_XDR_H)
  externC bool_t xdr_stringU16 ( XDR* xdrs, SAP_UTF16 **sp, u_int maxsize );
  #define xdr_stringU(xdrs, sp, maxsize) SAP_UNAME(xdr_string)(xdrs, sp, maxsize)
#endif /* different platforms */



/*-----------------------------------------------------------------------------
 * sapuc.h  -  _splitpath() (for NT only)
 *----------------------------------------------------------------------------*/

#ifdef SAPonNT
  #define _splitpathU16( path, drive, dir, fname, ext )  \
            _wsplitpath( path, drive, dir, fname, ext )
  #define _splitpathU( path, drive, dir, fname, ext ) \
            SAP_UNAME(_splitpath)( path, drive, dir, fname, ext )
#endif

/*-----------------------------------------------------------------------------
 * sapuc.h - re-definition of memcpy to check for overlapping buffers
 *           only in debug mode and only inside SAP (not in RFC SDK)
 *----------------------------------------------------------------------------*/
#if !defined(NDEBUG) && defined(SAPTYPE_H) && !(defined(SAPonOS400) && defined(SAPwithCHAR_EBCDIC))

  BEGIN_NS_STD_C_HEADER

    externC DECL_EXP void* memcpyRChk( void* pDst, const void* pSrc, size_t nLen, SAP_RAW* file, int line );
    #undef memcpyR
    #define memcpyR(t,s,l) memcpyRChk(t,s,l,(SAP_RAW*)cR(__FILE__),__LINE__)
    externC DECL_EXP void* memcpyUChk( SAP_UC* pDst, const SAP_UC* pSrc, size_t nLen, SAP_RAW* file, int line );
    #undef memcpyU
    #define memcpyU(t,s,l) memcpyUChk(t,s,l,(SAP_RAW*)cR(__FILE__),__LINE__)

  END_NS_STD_C_HEADER

#endif /* checked memcpy */


/*-----------------------------------------------------------------------------
 * sapuc.h - re-definition of the memory related functions in order
 *           to activate runtime Unicode debugger functionality
 *----------------------------------------------------------------------------*/
#if defined(SAPonAIX) && defined(SAPwithUNICODE) && defined(UNICODE_DEBUG)

  BEGIN_NS_STD_C_HEADER

    /* memory allocation functions  */
    externC void    * mallocRD  (           size_t, const SAP_RAW *, long );
    externC SAP_UC  * mallocUD  (           size_t, const SAP_RAW *, long );
    externC void    * reallocRD ( void *,   size_t, const SAP_RAW *, long );
    externC SAP_UC  * reallocUD ( SAP_UC *, size_t, const SAP_RAW *, long );
    externC void    * callocRD  ( size_t,   size_t, const SAP_RAW *, long );
    externC SAP_UC  * callocUD  ( size_t,   size_t, const SAP_RAW *, long );
    externC void      freeD     ( void *,           const SAP_RAW *, long );
    #define malloc(     len )         \
            mallocRD(  (len), (SAP_RAW *) __FILE__, __LINE__ )
    #define calloc(     num,   len )  \
            callocRD(  (num), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #define realloc(    ptr,   len )  \
            reallocRD( (ptr), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  mallocR
    #define mallocR(    len )         \
            mallocRD(  (len),        (SAP_RAW *) __FILE__, __LINE__ )
    #undef  mallocU
    #define mallocU(    len )         \
            mallocUD(  (len),        (SAP_RAW *) __FILE__, __LINE__ )
    #undef  callocR
    #define callocR(    num,   len )  \
            callocRD(  (num), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  callocU
    #define callocU(    num,   len )  \
            callocUD(  (num), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  reallocR
    #define reallocR(   ptr,   len )  \
            reallocRD( (ptr), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  reallocU
    #define reallocU(   ptr,   len )  \
            reallocUD( (ptr), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #define free( p )    freeD((void *)(p), (SAP_RAW *)__FILE__, __LINE__ )

    /* memory functions     */
    externC void     * memsetRD( void *,     int, size_t, const SAP_RAW*, long );
    externC SAP_CHAR * memsetUD( SAP_CHAR *, int, size_t, const SAP_RAW*, long );
    externC int        memcmpRD( const void *,     const void *,     size_t,
                                 const SAP_RAW *,  long );
    externC int        memcmpUD( const SAP_CHAR *, const SAP_CHAR *, size_t,
                                 const SAP_RAW *,  long );
    externC void*      memcpyRD(       void *,     const void *,     size_t,
                                 const SAP_RAW *,  long );
    externC SAP_CHAR * memcpyUD(       SAP_CHAR *, const SAP_CHAR *, size_t,
                                 const SAP_RAW*,   long );
    #undef  memsetR
    #define memsetR(   s,    c,    len )  \
            memsetRD( (s),  (c),  (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  memsetU
    #define memsetU(   s,    c,    len )  \
            memsetUD( (s),  (c),  (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  memcmpR
    #define memcmpR(   s1,   s2,   len ) \
            memcmpRD( (s1), (s2), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  memcmpU
    #define memcmpU(   s1,   s2,   len ) \
            memcmpUD( (s1), (s2), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  memcpyR
    #define memcpyR(   s1,   s2,   len ) \
            memcpyRD( (s1), (s2), (len), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  memcpyU
    #define memcpyU(   s1,   s2,   len ) \
            memcpyUD( (s1), (s2), (len), (SAP_RAW *) __FILE__, __LINE__ )

    /* string functions     */
    externC size_t   strlenUD( const SAP_UC *,
                               const SAP_RAW *, long );
    externC int      strcmpUD( const SAP_UC *,  const SAP_UC *,
                               const SAP_RAW *, long );
    externC SAP_UC * strcpyUD(       SAP_UC *,  const SAP_UC *,
                               const SAP_RAW *, long );
    #undef  strlenU
    #define strlenU(   p )        \
            strlenUD( (p),        (SAP_RAW *) __FILE__, __LINE__ )
    #undef  strcmpU
    #define strcmpU(   s1,   s2 ) \
            strcmpUD( (s1), (s2), (SAP_RAW *) __FILE__, __LINE__ )
    #undef  strcpyU
    #define strcpyU(   s1,   s2 ) \
            strcpyUD( (s1), (s2), (SAP_RAW *) __FILE__, __LINE__ )

  END_NS_STD_C_HEADER

#endif /* UNICODE_DEBUG */






/**********************************************************************/
/*                                                                    */
/* If you need C types to handle single characters or strings with a  */
/* large character set, you have the choice between six of them.      */
/* Please handle them distinctly! Some pairs may be compatible on     */
/* one platform but not on the others.                                */
/*                                                                    */
/* Each type has some advantages and some disadvantages. That is the  */
/* reason, why we could not drop any one.                             */
/*                                                                    */
/*                                                                    */
/*                                                                    */
/*                                                                    */
/*                        .---------.                                 */
/*                        | wchar_t |                                 */
/*                       .'         `----------.                      */
/*                       | XPG4 wide char      |                      */
/*                       | + "all" characters  |                      */
/*                       | + fast              |                      */
/*                       | - unknown coding    |                      */
/*                       | + many functions    |                      */
/*                       | - unknown size      |                      */
/*                       | + but size is fixed |                      */
/*                       `---------------------'                      */
/*                                                                    */
/*                                                                    */
/*                                                                    */
/*   .---------.                              .--------.              */
/*   |  char   |                              |   UC   |              */
/*  .'         `----------.                  .'        `-----------.  */
/*  | Standard C character|                  | universal character |  */
/*  | - 1 byte            |                  | + "all" characters  |  */
/*  | - variing coding    |                  | + fast              |  */
/*  | + many functions    |                  | - platform dependent|  */
/*  | - also used for     |                  | - unknown size      |  */
/*  |   multi-byte strings|                  | + but size is fixed |  */
/*  | - also used for     |                  | . zero-terminated   |  */
/*  |   raw bytes         |                  |   strings           |  */
/*  `---------------------'                  `---------------------'  */
/*                                                                    */
/*                                                                    */
/*                                                                    */
/*                                                                    */
/*   .---------.                              .--------.              */
/*   |   B8    |                              | CHAR   |              */
/*  .'         `----------.                  .'        `-----------.  */
/*  | multibyte           |                  | universal character |  */
/*  | - variable size     |                  | + "all" characters  |  */
/*  | - variing coding    |                  | + fast              |  */
/*  | + many functions    |                  | - platform dependent|  */
/*  | - cannot single char|                  | - unknown size      |  */
/*  | + 'char' compatible |                  | + but size is fixed |  */
/*  `---------------------'                  | . blank-padded      |  */
/*                                           |   strings           |  */
/*                                           `---------------------'  */
/*                                                                    */
/*                                                                    */
/**********************************************************************/


/**********************************************************************/
/*                                                                    */
/*  .----.  .------.  .------.  .---------.  .----.                   */
/*  | UC |  | CHAR |  | char |  | wchar_t |  | B8 |                   */
/*  `----'  `------'  `------'  `---------'  `----'                   */
/*                                                                    */
/* Beside of these three types there are some more character types:   */
/*                                                                    */
/*                                                                    */
/*   .--------.                                                       */
/*   |   U2   |                                                       */
/*  .'        `----------------.                                      */
/*  | ISO Unicode UCS-2        |            The real UCS-2            */
/*  | + 60000 characters       |                                      */
/*  | + coding = UCS-2         |                                      */
/*  | + size   = 2 B           |                                      */
/*  | - unknown byte order     |                                      */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .--------.                                                       */
/*   |  UTF8  |                                                       */
/*  .'        `----------------.                                      */
/*  | Unicode Transfer Format  |       Used within some database.     */
/*  | - variable size          |       Used in some files.            */
/*  | - cannot single char     |       Can be used for filenames.     */
/*  | + 2000000000 characters  |                                      */
/*  | + 'char' compatible      |                                      */
/*  | + "file system safe"     |                                      */
/*  | + easy UCS-2 convertable |                                      */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .--------.                                                       */
/*   |  UTF7  |                                                       */
/*  .'        `----------------.                                      */
/*  | Unicode Transfer Format  |       Used on some data stream.      */
/*  | - variable size          |       i.e. e-mail                    */
/*  | - cannot single char     |                                      */
/*  | + 2000000000 characters  |                                      */
/*  | + 'char' compatible      |                                      */
/*  | + 7-Bit ASCII compatible |                                      */
/*  | + "file system safe"     |                                      */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .--------.                                                       */
/*   |  UTF16 |                                                       */
/*  .'        `----------------.                                      */
/*  | Unicode Transfer Format  |       Unicode 2.0 (with surrogates)  */
/*  | - variable (even) size   |       ISO: UTF-16                    */
/*  | - cannot single char     |       Used in JAVA.                  */
/*  | + 1060000 characters     |                                      */
/*  | + UCS-2 compatible       |                                      */
/*  | + easy UCS-4 convertable |                                      */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .--------.                                                       */
/*   |   U4   |                                                       */
/*  .'        `----------------.                                      */
/*  | Unicode 4 byte Format    |       Unicode 2.0  &  ISO            */
/*  | + 2000000000 characters  |                                      */
/*  | + coding = UCS-4         |                                      */
/*  | + size   = 4 B           |                                      */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .------.                                                         */
/*   |  B7  |                                                         */
/*  .'      `------------------.                                      */
/*  | Character from 7-Bit set |       "Old C", US-ASCII              */
/*  | - single byte chars      |                                      */
/*  | . zero terminated strings|       Can be 8 bit if used on        */
/*  | + 'char' compatible      |       EBCDIC machine !               */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .------.                                                         */
/*   |  A7  |                                                         */
/*  .'      `------------------.                                      */
/*  | 7-bit-US-ASCII           |       US-ASCII                       */
/*  | - single byte chars      |                                      */
/*  | . zero terminated strings|       Is always ASCII. Even on an    */
/*  | + 'char' compatible      |       EBCDIC machine !               */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/*   .------.                                                         */
/*   |  E8  |                                                         */
/*  .'      `------------------.                                      */
/*  | 8-bit-IBM-500-EBCDIC     |       "international" EBCDIC         */
/*  | - single byte chars      |                                      */
/*  | . IBM-500 coding always  |       even in other countries        */
/*  | + 'char' compatible      |                                      */
/*  `--------------------------'                                      */
/*                                                                    */
/*                                                                    */
/**********************************************************************/


/**********************************************************************/
/* wchar_t :   wide character for fast processing                     */
/*             with platform dependent coding.                        */
/*--------------------------------------------------------------------*/
/* This is the C data type as defined by XPG4.                        */
/* A variable of this type can store a wide character.                */
/* The size of this type is platform dependent: often 2 or 4 bytes.   */
/* The coding used is platform dependent and OS release specific.     */
/*--------------------------------------------------------------------*/
/* This type gives direct access to many functions, as has been       */
/* defined in XPG4 and should be implemented everywhere.              */
/*    Classification of a single character:                           */
/*       iswalnum                                                     */
/*       iswalpha                                                     */
/*       iswcntrl                                                     */
/*       iswupper      (Note: most scripts do not have cases.)        */
/*       iswlower                                                     */
/*       iswdigit                                                     */
/*       iswprint                                                     */
/*       wcwidth                                                      */
/*    Simple handling of w-zero terminated strings:                   */
/*       wcscat / wcsncat                                             */
/*       wcscmp / wcsncmp                                             */
/*       wcscpy / wcsncpy                                             */
/*       wcslen                                                       */
/*       wcschr / wcsrchr                                             */
/*       wcspbrk                                                      */
/*       wcsspn / wcscspn                                             */
/*       wcswcs                                                       */
/*       wcstok / wcstok_r                                            */
/*       wcswidth                                                     */
/*    Locale dependent handling of w-zero terminated strings:         */
/*       wcscoll                                                      */
/*       wcsxfrm                                                      */
/*    Conversion functions:                                           */
/*       wcstod / wcstol / wcstoul                                    */
/*       mbtowc / mbstowcs / wctomb / wcstombs                        */
/* Note:                                                              */
/*       wcsftime cannot be used!                                     */
/*--------------------------------------------------------------------*/


/**********************************************************************/
/* SAP_UC:   universal character                                      */
/*--------------------------------------------------------------------*/
/* The size of an universal character is constant and platform        */
/* dependent.                                                         */
/* The coding is platfrom dependent also.                             */
/* It is implementations dependent, wether the coding can vary during */
/* runtime ! ( see setlocale() ).                                     */
/* It is implementations dependent, how many distinct characters can  */
/* be stored. But often all important characters of the world are     */
/* possible.                                                          */
/* To give an idea, why there is this distinction between declared    */
/* features and those which are left 'implementations dependent':     */
/* A specific implementation may map 'SAP_UC' onto                    */
/*  + UCS-2  (16-Bit Unicode, most likely)                            */
/*  + UTF-16 in 32-Bit                                                */
/*  + wchar_t with some propietary coding                             */
/*  + Latin-1 or some other ISO-8859-1 single byte code               */
/*                                                                    */
/* This type gives access to many SAP specific functions.             */
/*--------------------------------------------------------------------*/


/**********************************************************************/
/* SAP_U2:   character for Unicode UCS-2                              */
/*--------------------------------------------------------------------*/
/* A variable of this type can store a Unicode UCS-2 character.       */
/* The size of this type is 16 bit.                                   */
/* The coding used is UCS-2 (ISO 10646). The release of that          */
/* ISO norm is not specified here. It is the most recent release that */
/* is supported by SAP.                                               */
/* If not explicitelly labeled UTF-16 or SAP_UTF16, surrogates are    */
/* neither expected nor handled.                                      */
/* Comparison to SAP_UTF16: SAP_U2 should be used when surrogate      */
/* support is explicitely exluded. Otherwise, use SAP_UTF16.          */
/*--------------------------------------------------------------------*/
/* This type gives access to some generic functions, which are        */
/* handled differently on the different platforms, but give the same  */
/* result to all SAP applications.                                    */
/*    Classification of a single character:                           */
/*       <none. Processing is done using SAP_UC.>                     */
/*    Simple handling of zero terminated strings:                     */
/*       <none. Processing is done using SAP_UC.>                     */
/*    Conversion functions:                                           */
/*       SAP_U2_...                                                   */
/*--------------------------------------------------------------------*/

#define U2Null ((SAP_U2)0)

#if defined(WCHAR_is_2B)
  typedef wchar_t      SAP_U2;
#elif defined(SAP_UC_is_char16)
  typedef char16_t     SAP_U2;
#else
  typedef SAP_USHORT   SAP_U2 ;
#endif

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_U4:   character for Unicode UCS-4 (UTF-32)                     */
/*--------------------------------------------------------------------*/
/* A variable of this type can store a Unicode UCS-4 or UTF-32        */
/* character. UTF-32 is a subset of Ucs-4 that contains exacly the    */
/* same characters as UTF-16. We do not explicitely distinguish       */
/* between UTF-32 and UCS-4 in the C code.                            */
/* The size of this type is 32 bit.                                   */
/* The coding used is UCS-4 (ISO 10646). The release of that          */
/* ISO norm is not specified here. It is the most recent release that */
/* is supported by SAP. UTF-32 is the subset of UCS-4 that contains   */
/* exactly the same characters as UTF-16. We do not explicitely       */
/* distinguish between UTF-32 and UCS-4 in the C code.                */
/*--------------------------------------------------------------------*/
/* This type gives access to some generic functions, which are        */
/* handled differently on the different platforms, but give the same  */
/* result to all SAP applications.                                    */
/*    Classification of a single character:                           */
/*       <none. Processing is done using SAP_UC.>                     */
/*    Simple handling of zero terminated strings:                     */
/*       <none. Processing is done using SAP_UC.>                     */
/*    Conversion functions:                                           */
/*       SAP_U4_...                                                   */
/*--------------------------------------------------------------------*/

#define U4Null ((SAP_U4)0)

#if defined(WCHAR_is_4B)
  typedef wchar_t   SAP_U4;
#else
  typedef SAP_UINT   SAP_U4 ;
#endif

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_B8:   bytes storing multibyte characters                       */
/*--------------------------------------------------------------------*/
/* This type cannot be used to define a variable for a single         */
/* character !                                                        */
/* A string of this type can store characters using one or more bytes */
/* for each character.                                                */
/* The coding varies during runtime ! ( see setlocale() ).            */
/* The type SAP_B8 is compatible to char. It is used for              */
/* documentation purposes. It marks char[] which may contain          */
/* multibyte characters.                                              */
/*--------------------------------------------------------------------*/
/* This type gives direct access to many functions, as has been       */
/* defined in ANSI C and XPG4 and should be implemented everywhere.   */
/*    Classification of a single character:                           */
/*       mblen                                                        */
/*    Simple handling of zero terminated strings:                     */
/*       strcat                                                       */
/*       strcmp                                                       */
/*       strcpy                                                       */
/*       strlen    (not number of chars, but number of bytes!)        */
/*    Conversion functions:                                           */
/*       strcoll / strxfrm                                            */
/*       mbtowc / mbstowcs / wctomb / wcstombs                        */
/* Note:                                                              */
/* The character classification functions isprint, isalpha,.. are     */
/* only valid, if(mblen(ptr)==1)                                      */
/*--------------------------------------------------------------------*/

typedef char   SAP_B8 ;
#define        B8Null   ((SAP_B8)0)

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_UTF8:   bytes storing multibyte characters with UTF-8 coding   */
/*--------------------------------------------------------------------*/
/* This type cannot be used to define a variable for a single         */
/* character !                                                        */
/* A string of this type can store characters using one or more bytes */
/* for each character.                                                */
/* The coding is defined with Unicode.                                */
/* The type SAP_UTF8 is compatible to char. It is used for            */
/* documentation purposes. It marks char[] which may contain          */
/* UTF-8 multibyte characters.                                        */
/*--------------------------------------------------------------------*/
/* This type gives direct access to some functions, as has been       */
/* defined in ANSI C and XPG4 and should be implemented everywhere.   */
/*    Simple handling of zero terminated strings:                     */
/*       strcat                                                       */
/*       strcmp                                                       */
/*       strcpy                                                       */
/*       strlen    (not number of chars, but number of bytes!)        */
/*--------------------------------------------------------------------*/

typedef unsigned char   SAP_UTF8 ;
#define                 UTF8Null    ((SAP_UTF8)0)

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_CESU8:  similar to UTF8, preserving UTF-16 binary collation    */
/*--------------------------------------------------------------------*/
/* Cf http://www.unicode.org/reports/tr26/                            */
/* "... 8-bit Compatibility Encoding Scheme for UTF-16 (CESU) that is */
/* intended for internal use within systems processing Unicode        */
/* in order to provide an ASCII-compatible 8-bit encoding that        */
/* is similar to UTF-8 but preserves UTF-16 binary collation.         */
/* It is not intended nor recommended as an encoding used for         */
/* open information exchange. The Unicode Consortium, does not        */
/* encourage the use of CESU-8, but does recognize the existence of   */
/* data in this encoding and supplies this technical report to        */
/* clearly define the format and to distinguish it from UTF-8.        */
/* This encoding does not replace or amend the definition of UTF-8.   */
/*--------------------------------------------------------------------*/
/* Conversion UTF-16 <> CESU-8: rscputf.h                             */
/*--------------------------------------------------------------------*/

typedef unsigned char   SAP_CESU8 ;
#define                 CESU8Null    ((SAP_CESU8)0)


/**********************************************************************/
/* SAP_UTF7:   bytes storing multibyte characters with UTF-7 coding   */
/*--------------------------------------------------------------------*/
/* This type cannot be used to define a variable for a single         */
/* character !                                                        */
/* A string of this type can store characters using one or more bytes */
/* for each character.                                                */
/* The coding is defined with Unicode.                                */
/* The type SAP_UTF7 is compatible to char. It is used for            */
/* documentation purposes. It marks char[] which may contain          */
/* UTF-7 multibyte characters.                                        */
/* Note: UTF-7 encoding has modes! You always have to convert a whole */
/*       chunck of data (i.e. whole lines)                            */
/*--------------------------------------------------------------------*/
/* This type gives direct access to some functions, as has been       */
/* defined in ANSI C and XPG4 and should be implemented everywhere.   */
/*    Simple handling of zero terminated strings:                     */
/*       strlen    (not number of chars, but number of bytes!)        */
/*--------------------------------------------------------------------*/

typedef unsigned char   SAP_UTF7 ;
#define                 UTF7Null     ((SAP_UTF7)0)

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_A7:   a byte storing a 7-bit-US-ASCII character                */
/*--------------------------------------------------------------------*/
/* The coding is defined as 7-Bit US-ASCII. This is platform          */
/* independent. Even on an EBCDIC machine, variables of type SAP_A7   */
/* contain ASCII. Also it never contains national characters.         */
/* SAP_A7 values are compatible to UTF-8. (Only one direction.)       */
/* When text fields of SAP_A7 are defined, we expect a terminating    */
/* null.                                                              */
/* SAP_A7_A has same implementation as SAP_A7. It shall be used, when */
/* blank-padded non-terminated text fields are defined.               */
/*--------------------------------------------------------------------*/

typedef char   SAP_A7;
#define        A7Null   ((SAP_A7)0)

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_B7:   byte storing an English character or simple symbol       */
/*--------------------------------------------------------------------*/
/* The coding is defined either 7-Bit US-ASCII or a subset of EBCDIC. */
/* The type SAP_B7 is compatible to char. It is used for              */
/* documentation purposes. It marks char[] which never contain        */
/* national characters.                                               */
/*--------------------------------------------------------------------*/

typedef char SAP_B7;
#define      B7Null    ((SAP_B7)0)

/* All other routines are in "sapuc2.h". */


/**********************************************************************/
/* SAP_E8:   a byte storing a 7-bit-US-ASCII character                */
/*--------------------------------------------------------------------*/
/* The coding is defined as 8-Bit IBM 500 EBCDIC. This is platform    */
/* independent. Even on an ASCII machine, variables of type SAP_E8    */
/* contain EBCDIC. If it contains national characters, these are from */
/* the western European area.                                         */
/* When text fields of SAP_E8 are defined, we expect a terminating    */
/* null.                                                              */
/* SAP_E8_A has same implementation as SAP_E8. It shall be used, when */
/* blank-padded non-terminated text fields are defined.               */
/*--------------------------------------------------------------------*/

#if defined (SAPonOS400) || defined (SAPwithPASE400)
  typedef          char   SAP_E8;
#else /* normal UNIX or NT */
  typedef unsigned char   SAP_E8;
#endif
#define                   E8Null   ((SAP_E8)0)


/**********************************************************************/
/* SAP_UC_MB: multibyte character representation of SAP_UC            */
/*--------------------------------------------------------------------*/
/* This type contains the multibyte character representation          */
/* of SAP_UC                                                          */
/* - In Unicode mode this is UTF-8.                                   */
/* - In non-Unicode mode the encoding is determined by the active     */
/*   codepage ( see setlocale() ) and thereby varies during runtime.  */
/* The type SAP_UC_MB is compatible to char and can be used to call   */
/* platform functions if they support UTF-8.                          */
/*--------------------------------------------------------------------*/

typedef char            SAP_UC_MB;
#define                 UCMBNull   ((SAP_UC_MB)0)

/* All other routines are in "sapuc2.h". */


/*-----------------------------------------------------------------------------
 * sapuc.h  -  Function to print trace and error messages.
 * Further documentation in flat/nlsuidoc.htm
 *----------------------------------------------------------------------------*/
typedef enum
{ none = 0,
  low = 1,
  medium = 4,
  high = 16
} NlsuiTraceLevel ;

typedef void (* TRACE_FUNC_T)  ( const SAP_B7 *  buffer,
                                 int             number_of_chars );

externC void CDCL_U nlsui_set_trace( TRACE_FUNC_T p, NlsuiTraceLevel l );
externC void CDCL_U nlsui_set_trace_func( TRACE_FUNC_T p );


/*-----------------------------------------------------------------------------
 * sapuc.h  -   Functions that test character properties (ctype functions)
 *
 *   These function declarations are located after the typedefs for
 *   SAP_U4, because we use SAP_U4 for the ICU function declarations.
 *
 *   sizeofR(c) is not evaluated at run time. Therefore these macro definitions
 *   are no problem in expressions like isprint(c++).
 *----------------------------------------------------------------------------
 * __SAP_DLL_DECLSPEC is a marker for symbols that must be imported from a
 * shared library. It is necessary
 * - only on NT
 * - only for variables (function pointers), not for functions
 * - only if the port-library comes as part of a shared library. To activate it
 * on NT, set the Macro __SAP_DESIGNATED_DLL (or use sapucx.h).
 * See also saptype.h.
 *----------------------------------------------------------------------------*/

typedef signed char          ICU_BOOL;
#define isdigit09( c )       ((unsigned int)((c)-cU('0')) <  10)
#define isxdigit0F(c)        (((c) >= cU('0') && (c) <= cU('9')) ||        \
                              ((c) >= cU('A') && (c) <= cU('F')) ||        \
                              ((c) >= cU('a') && (c) <= cU('f')))

#define isxxxNUC(isfctnuc,c)   ( sizeofR(c) == sizeofR(SAP_CHAR) ?  \
                               isfctnuc(U_CHAR(c)):                 \
                               /*LINTED_SIGNEDCHAR*/isfctnuc(c)     )

#ifndef SAPwithUNICODE
  #define isalnumU(c)        isxxxNUC(isalnum,c)
  #define isasciiU(c)        isxxxNUC(isascii,c)
  #define isalphaU(c)        isxxxNUC(isalpha,c)
  #define iscntrlU(c)        isxxxNUC(iscntrl,c)
  #define isdigitU(c)        isxxxNUC(isdigit09,c)
  #define isgraphU(c)        isxxxNUC(isgraph,c)
  #define islowerU(c)        isxxxNUC(islower,c)
  #define isprintU(c)        isxxxNUC(isprint,c)
  #define ispunctU(c)        isxxxNUC(ispunct,c)
  #define isspaceU(c)        isxxxNUC(isspace,c)
  #define isupperU(c)        isxxxNUC(isupper,c)
  #define isxdigitU(c)       isxxxNUC(isxdigit0F,c)
#else /* Now SAPwithUNICODE */

  #define isasciiU( c ) isascii( c )
  #define isdigitU( c ) isdigit09( c )


  #if defined (SAPwithICU)
    /* We use the external functions provided in ICU */
    /* The function pointers are mapped in mainU().  */
    BEGIN_NS_STD_C_HEADER
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *isalnumU)( SAP_U4 c );
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *isalphaU)( SAP_U4 c );
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *iscntrlU)( SAP_U4 c );
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *islowerU)( SAP_U4 c );
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *isprintU)( SAP_U4 c );
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *isspaceU)( SAP_U4 c );
      externC __SAP_DLL_DECLSPEC ICU_BOOL (CDCL_U *isupperU)( SAP_U4 c );
    END_NS_STD_C_HEADER

    /* The following functions are missing in ICU. They are implemented
     *  in nlsui1.c, using the existing ICU ctype functions.  */
    BEGIN_NS_STD_C_HEADER
      externC DECL_EXP ICU_BOOL CDCL_U isgraphU   ( SAP_U4 c );
      externC ICU_BOOL CDCL_U ispunctU   ( SAP_U4 c );
      externC ICU_BOOL CDCL_U isxdigitU  ( SAP_U4 c );
    END_NS_STD_C_HEADER

  #else /* not ICU */
    /* A cast to wint_t (16-bit) is needed. Otherwise the compiler issues
     * "integral size mismatch in argument" if c is an int. */
    #define isalnumU(c)        iswalnum(NT_CAST(wint_t)(c))
    #define isalphaU(c)        iswalpha(NT_CAST(wint_t)(c))
    #define iscntrlU(c)        iswcntrl(NT_CAST(wint_t)(c))
    #define islowerU(c)        iswlower(NT_CAST(wint_t)(c))
    #define isgraphU(c)        iswgraph(NT_CAST(wint_t)(c))
    #define isprintU(c)        iswprint(NT_CAST(wint_t)(c))
    #define ispunctU(c)        iswpunct(NT_CAST(wint_t)(c))
    #define isspaceU(c)        iswspace(NT_CAST(wint_t)(c))
    #define isupperU(c)        iswupper(NT_CAST(wint_t)(c))
    #define isxdigitU(c)       iswxdigit(NT_CAST(wint_t)(c))
  #endif /* SAPwithICU or not */

#endif /* SAPwithUNICODE */


#if defined(SAPccQ) && defined(SAPonNT)
  /* ccQ requires that if function is a realized as macro that there is a real
   * function behind the macro. This is not the case for isascii on NT.
   * Therefore we declare a prototype ourselves here.
   */
  BEGIN_NS_STD_C_HEADER
    #undef isascii
    externC int isascii ( int c );
  END_NS_STD_C_HEADER
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -   toupper and tolower
 *----------------------------------------------------------------------------*/
#ifndef SAPwithUNICODE

  #define tolowerU(c)        ( sizeof(c) == SAP_UC_LN \
                               ? tolower(U_CHAR(c))   \
                               : /*LINTED_SIGNEDCHAR*/ tolower(c) )
  #define toupperU(c)        ( sizeof(c) == SAP_UC_LN \
                               ? toupper(U_CHAR(c))   \
                               : /*LINTED_SIGNEDCHAR*/ toupper(c) )

#else /* Now SAPwithUNICODE */

  #if defined (SAPwithICU)
    BEGIN_NS_STD_C_HEADER
      externC __SAP_DLL_DECLSPEC SAP_U4 (CDCL_U *tolowerU)( SAP_U4  c );
      externC __SAP_DLL_DECLSPEC SAP_U4 (CDCL_U *toupperU)( SAP_U4  c );
    END_NS_STD_C_HEADER

  #else /* not ICU */
    #if defined(SAPonNT)
      /* A cast to wint_t (16-bit) is needed. Otherwise the compiler issues
       * "integral size mismatch in argument" if c is an int. */
      #define tolowerU(c)        towlower((wint_t)(c))
      #define toupperU(c)        towupper((wint_t)(c))

    #else
      /* We use the w-functions even for SAP_UC_is_UTF16_without_wchar */
      #define tolowerU(c)        towlower(c)
      #define toupperU(c)        towupper(c)

    #endif /* different platforms */

  #endif /* SAPwithICU or not */
#endif /* SAPwithUNICODE */


/*
 * TOUPPERU, TOLOWERU: macro versions of toupperU and tolowerU,
 * optimized for 7bit ASCII
 */
#define TOLOWERU_A7(c)   ( (c) > 0x40 && (c) < 0x5B ? ((c)+0x20) : (c) )
#define TOUPPERU_A7(c)   ( (c) > 0x60 && (c) < 0x7B ? ((c)-0x20) : (c) )

#ifndef SAPwithUNICODE
  #if defined(SAPwithCHAR_ASCII) && !defined(SAPonLIN)
    /* On Linux, the system functions are faster */
    #define TOLOWERU(c)      ( ((c) & 0x80) == 0 ? TOLOWERU_A7(c) \
                                                 : tolowerU(c) )
    #define TOUPPERU(c)      ( ((c) & 0x80) == 0 ? TOUPPERU_A7(c) \
                                                 : toupperU(c) )
  #else 
    #define TOLOWERU(c)      tolowerU(c)
    #define TOUPPERU(c)      toupperU(c)
  #endif

#else /* now SAPwithUNICODE */
  #define TOLOWERU(c)        ( ((c) & 0xFF80) == 0 ? TOLOWERU_A7(c) \
                                                   : tolowerU(c) )
  #define TOUPPERU(c)        ( ((c) & 0xFF80) == 0 ? TOUPPERU_A7(c) \
                                                   : toupperU(c) )

#endif /* SAPwithUNICODE */


/*-----------------------------------------------------------------------------
 *
 * sapuc.h  -   Declaration and Implementation of functions which must be in
 *              the same translation unit as the code which calls them.
 *----------------------------------------------------------------------------*/

/*-----------------------------------------------------------------------------
 * sapuc.h  -  struct stat_U and functions statU, lstatU, fstatU
 *
 * struct stat_U must be used on OS/400, because struct stat contains a
 * char array. On the other platforms, stat_U and stat are identical.
 *
 * Attention:  SAPUC_H_WITH_statU must be #defined BEFORE including sapuc.h.
 *----------------------------------------------------------------------------*/
#if defined(SAPUC_H_WITH_statU)   || defined(SAPUC_H_WITH_lstatU) || \
    defined(SAPU16C_WITH_statU16) || defined(SAPU16C_WITH_lstatU16)

  #include <sys/stat.h>   /* In case it has not yet been included. This file
                           * may define 'stat' to be 'stat64', for example.
                           */
  /*---------------------------------------------------------------------------
   * sapuc.h - declaration part for statU, lstatU etc.
   *--------------------------------------------------------------------------*/

  #define stat_U                          SAP_UNAME_UR(stat_)

  #define statU16_RETURN                  int
  #define statU16_TPARAMS                 (const SAP_UTF16 *path, struct stat_U16 *buffer)
  #define statU16_PARAMS                  (path, buffer)
  #define statU(path, buffer)             SAP_UNAME_(stat)(path, buffer)
  #define _statU(path, buffer)            SAP_UNAME_(stat)(path, buffer)

  #define fstatU(fdes, buffer)            SAP_UNAME_(fstat)(fdes, buffer)

  #define lstatU16_RETURN                 int
  #define lstatU16_TPARAMS                (const SAP_UTF16 *path, struct stat_U16 *buffer)
  #define lstatU16_PARAMS                 (path, buffer)
  #define lstatU(path, buffer)            SAP_UNAME_(lstat)(path, buffer)

  #ifdef SAPonOS400
    #define stat_R                        stat
    #if defined(EXT_RELEASE)
    struct stat_U16 {
      mode_t          st_mode;
      ino_t           st_ino;
      uid_t           st_uid;
      gid_t           st_gid;
      long long       st_size;
      long long       st_atime;
      long long       st_mtime;
      long long       st_ctime;
      dev_t           st_dev;
      long long       st_blksize;
	  nlink_t         st_nlink;
	  unsigned short  st_codepage;
      unsigned long long st_allocsize;
	  unsigned int    st_ino_gen_id;
      SAP_UC          st_objtype[11];
      unsigned short  st_ccsid;
    };
	#else
    struct stat_U16 {
      mode_t          st_mode;
      ino_t           st_ino;
      nlink_t         st_nlink;
      uid_t           st_uid;
      gid_t           st_gid;
      off_t           st_size;
      time_t          st_atime;
      time_t          st_mtime;
      time_t          st_ctime;
      dev_t           st_dev;
      size_t          st_blksize;
      unsigned long   st_allocsize;
      SAP_UC          st_objtype[11];
      unsigned short  st_ccsid;
      unsigned short  st_codepage;
      unsigned int    st_ino_gen_id;
    };
	#endif
    SAP_U16_PROTOTYPE(stat)
    externC int fstatU16 ( int filedes, struct stat_U16 *buffer );
    SAP_U16_PROTOTYPE(lstat)
  #elif defined(SAPonNT)
    #define stat_R                        _stat
    #define stat_U16                      _stat
    #define statU16                       _wstat
    #define fstatU16( fdes, buffer )      _fstat( fdes, buffer )
    /* no lstat */
  #else
    #define stat_R                        stat
    #define stat_U16                      stat
    SAP_U16_PROTOTYPE_STAT(stat)
    #define fstatU16( fdes, buffer )      fstat( fdes, buffer )
    SAP_U16_PROTOTYPE_STAT(lstat)
  #endif


  /*---------------------------------------------------------------------------
   * sapuc.h - implementation part for statU, lstatU etc.
   *
   * stat() can be a macro which maps to different functions, depending
   * on feature-test macros (e.g. Tru64). sizeof(struc stat) and the
   * sizes of its members may also depend on feature-test macros.
   * The only way to ensure that users of statU() make the same assumptions
   * on struct stat as statU() itself is to have everything in one
   * translation unit.
   *--------------------------------------------------------------------------*/

  #include <errno.h>
  externC DECL_EXP size_t U2sToUtf8s (char *     , const SAP_UTF16 *, size_t);
  #define nlsui_u2conv_error(dest, src, len, fileId, line)  do ; while(0)

  #if (defined(SAPUC_H_WITH_statU) && defined(SAPwithUNICODE)) || \
      defined(SAPU16C_WITH_statU16)
  #if defined(SAPonUNIX)

  static int statU16 ( const SAP_UTF16 *wpath, struct stat_U *buffer )
  {
    char cpath[MAX_PATH_LN];
    char *cpath1Ptr;
    size_t nchar;

    if (NULL == wpath) cpath1Ptr = NULL;
    else
    {
      nchar = U2sToUtf8s(cpath, wpath, MAX_PATH_LN);
      if ((size_t)-1 == nchar)
      {
        nlsui_u2conv_error(cpath, wpath, MAX_PATH_LN, __FILE__, __LINE__);
        return -1;
      }
      if( (size_t)MAX_PATH_LN == nchar )
      {
        errno = ENAMETOOLONG;
        return -1;
      }
      cpath1Ptr = cpath;
    }
    return stat(cpath1Ptr, buffer);
  } /*  statU() */

  #endif /* platform */
  #endif /* SAPUC_H_WITH_statU */

  #if (defined(SAPUC_H_WITH_lstatU) && defined(SAPwithUNICODE)) || \
       defined(SAPU16C_WITH_lstatU16)
  #if defined(SAPonUNIX)

  static int lstatU16 ( const SAP_UTF16 *wpath, struct stat_U *buffer )
  {
    char cpath[MAX_PATH_LN];
    char *cpath1Ptr;
    size_t nchar;

    if (NULL == wpath) cpath1Ptr = NULL;
    else
    {
      nchar = U2sToUtf8s(cpath, wpath, MAX_PATH_LN);
      if ((size_t)-1 == nchar)
      {
        nlsui_u2conv_error(cpath, wpath, MAX_PATH_LN, __FILE__, __LINE__);
        return -1;
      }
      if( (size_t)MAX_PATH_LN == nchar )
      {
        errno = ENAMETOOLONG;
        return -1;
      }
      cpath1Ptr = cpath;
    }
    return lstat(cpath1Ptr, buffer);
  } /*  lstatU() */

  #endif /* platform */
  #endif /* SAPUC_H_WITH_lstatU */

#endif /* SAPUC_H_WITH_statU etc */

/*-----------------------------------------------------------------------------
 * sapuc.h  -   undef CDCL_U
 *----------------------------------------------------------------------------*/
#undef CDCL_U


/*-----------------------------------------------------------------------------
 * sapuc.h  -   special (re)definitions for AS/400
 *----------------------------------------------------------------------------*/
#if defined(SAPonOS400) || defined(SAPwithPASE400)
    /* ts: for AS/400 and PASE we popenU->as4_popenU, pclose->as4_pclose
     * (Notice that this in itself isn't sufficient though, you still need to
     * use as4_fgetsU/as4_freadU instead of fgetsU and freadU, otherwise
     * you'll get EBCDIC garbage
     * Notice that these function prototypes are copies from as4exec.h */
    externC FILE* as4_popenU ( const SAP_UC* command, const SAP_UC* type );
    externC int as4_pclose ( FILE* f );
    externC size_t as4_freadU ( SAP_UC* buffer, size_t size, size_t count, FILE* f );
    externC SAP_UC* as4_fgetsU ( SAP_UC* string, int n, FILE* f );
	externC int as4_fputsU ( const SAP_UC* string, FILE* f );
	externC int as4_fputcU ( int c, FILE* f );
	externC int as4_fprintfU ( FILE* f, const SAP_UC* format, ... );
	externC SAP_A7* setlocalePASE(int cat, const SAP_A7* locale);
	externC SAP_UC* as4_ctime64 ( const time_t* timer );
    externC SAP_UC* as4_ctime64_r ( const time_t* timer, SAP_CHAR* res );
    #undef  popenU
	#undef  freadU
	#undef  fgetsU
	#undef  fputsU
	#undef  fputcU
	#undef  fprintfU
    #define popenU as4_popenU
    #define pclose as4_pclose
	#define freadU as4_freadU
	#define fgetsU as4_fgetsU
	#define fputsU as4_fputsU
	#define fputcU as4_fputcU
	#define fprintfU as4_fprintfU
	#define o4freadU(buf, s, n, stream)  SAP_UNAME(fread)(buf, s, n, stream)
	#define o4fgetsU(s, n, stream)       SAP_UNAME(fgets)(s, n, stream)
	#define o4fputsU(s, stream)          SAP_UNAME(fputs)(s, stream)
	#define o4fputcU(c, stream)          SAP_UNAME(fputc)(c, stream)
	#define o4fprintfU                   SAP_UNAME(fprintf)
	#if defined(SAPonOS400) && defined(EXT_RELEASE)
	#undef  ctimeU
	#undef  ctime_rU
	#define ctimeU   as4_ctime64
	#define ctime_rU as4_ctime64_r
	#endif
	#define O4TRC_WITHOUT_WORK_AREA
#endif


/*-----------------------------------------------------------------------------
 * sapuc.h  -   Securelib Starts here-
 *----------------------------------------------------------------------------*/

/* SECURE_NAME: name switching between Unicode and NonUnicode compilation mode
 * for Securelib functions
 */
/*Securelib in NT may come first*/
/*#ifdef SAPonNT
  #define SECURE_NAME(name)        name
#else*/
  #define SECURE_NAME(name)        name##RFB
/*#endif*/

/*strnlen*/
externC DECL_EXP size_t strnlenRFB(const char *s, size_tR maxsize);
#define strnlenR(  s, maxsize )               SECURE_NAME(strnlen)(  s, maxsize )
#define strnlenaR( s )                        SECURE_NAME(strnlen)(  s, sizeofR(s) )
externC DECL_EXP size_t strnlenU16(const SAP_UTF16 *s, size_tU maxsize);
#define strnlenU(  s, s1max )                 SAP_UNAME_UR(strnlen)( s, s1max )
#define strnlenaU( s )                        SAP_UNAME_UR(strnlen)( s, sizeofU(s) )

/*strcpy_s*/
externC DECL_EXP int strcpy_sRFB(char * s1, size_tR s1max, const char * s2);
#define strcpy_sR(  s1, s1max, s2 )           SECURE_NAME(strcpy_s)(  s1, s1max, s2 )
#define strcpy_saR( s1, s2 )                  SECURE_NAME(strcpy_s)(  s1, sizeofR(s1), s2 )
externC DECL_EXP int strcpy_sU16(SAP_UTF16 * dest, size_tU s1max, const SAP_UTF16 * src);
#define strcpy_sU(  s1, s1max, s2 )           SAP_UNAME_UR(strcpy_s)( s1, s1max, s2 )
#define strcpy_saU( s1, s2 )                  SAP_UNAME_UR(strcpy_s)( s1, sizeofU(s1), s2 )

/*strncpy_s*/
externC DECL_EXP int strncpy_sRFB(char * s1, size_tR s1max, const char * s2, size_t n);
#define strncpy_sR(  s1, s1max, s2, n )       SECURE_NAME(strncpy_s)(  s1, s1max, s2, n )
#define strncpy_saR( s1, s2, n )              SECURE_NAME(strncpy_s)(  s1, sizeofR(s1), s2, n )
externC DECL_EXP int strncpy_sU16(SAP_UTF16 * dest, size_tU s1max, const SAP_UTF16 * src, size_t n);
#define strncpy_sU(  s1, s1max, s2, n )       SAP_UNAME_UR(strncpy_s)( s1, s1max, s2, n )
#define strncpy_saU( s1, s2, n )              SAP_UNAME_UR(strncpy_s)( s1, sizeofU(s1), s2, n )

/*strcat_s*/
externC DECL_EXP int strcat_sRFB(char * s1, size_tR s1max, const char * s2);
#define strcat_sR(  s1, s1max, s2 )           SECURE_NAME(strcat_s)(  s1, s1max, s2 )
#define strcat_saR( s1, s2 )                  SECURE_NAME(strcat_s)(  s1, sizeofR(s1), s2 )
externC DECL_EXP int strcat_sU16(SAP_UTF16 * dest, size_tU s1max, const SAP_UTF16 * src);
#define strcat_sU(  s1, s1max, s2 )           SAP_UNAME_UR(strcat_s)( s1, s1max, s2 )
#define strcat_saU( s1, s2 )                  SAP_UNAME_UR(strcat_s)( s1, sizeofU(s1), s2 )

/*strncat_s*/
externC DECL_EXP int strncat_sRFB(char * s1, size_tR s1max, const char * s2, size_tR n);
#define strncat_sR(  s1, s1max, s2, n )       SECURE_NAME(strncat_s)(  s1, s1max, s2, n )
#define strncat_saR( s1, s2, n )              SECURE_NAME(strncat_s)(  s1, sizeofR(s1), s2, n )
externC DECL_EXP int strncat_sU16(SAP_UTF16 * dest, size_tU s1max, const SAP_UTF16 * src, size_tU n);
#define strncat_sU(  s1, s1max, s2, n )       SAP_UNAME_UR(strncat_s)( s1, s1max, s2, n )
#define strncat_saU( s1, s2, n )              SAP_UNAME_UR(strncat_s)( s1, sizeofU(s1), s2, n )

/*gets_s*/
externC DECL_EXP char * gets_sRFB(char *s, size_tR n);
#define gets_sR(  s, n )                      SECURE_NAME(gets_s)(  s, n )
#define gets_saR( s )                         SECURE_NAME(gets_s)(  s, sizeofR(s) )
externC DECL_EXP SAP_UTF16 * gets_sU16(SAP_UTF16 *s, size_tU n);
#define gets_sU(  s, n )                      SAP_UNAME_UR(gets_s)( s, n )
#define gets_saU( s)                          SAP_UNAME_UR(gets_s)( s, sizeofU(s) )

/*the scanf family for RFB, commented currently*/
/* int scanf_sRFB(const char * format, ...);
 * int vscanf_sRFB(const char * format, va_list arg);
 * int fscanf_sRFB(FILE * stream, const char * format, ...);
 * int vfscanf_sRFB(FILE * stream, const char * format, va_list arg);
 * int sscanf_sRFB(const char * s, const char * format, ...);
 * int vsscanf_sRFB(const char * s, const char * format, va_list arg);
 * #define scanf_sR                        SECURE_NAME(scanf_s)
 * #define vscanf_sR                       SECURE_NAME(vscanf_s)
 * #define fscanf_sR                       SECURE_NAME(fscanf_s)
 * #define sscanf_sR                       SECURE_NAME(sscanf_s)
 * #define vsscanf_sR                      SECURE_NAME(vsscanf_s)
 * #define sscanf_sR                       SECURE_NAME(sscanf_s)
 */

/*sscanf_sU*/
/* int sscanf_sU16(const SAP_UTF16 *s, const SAP_UTF16 *format, ...);
 */
#define sscanf_sU16_RETURN             intU
#define sscanf_sU16_TPARAMS            (const SAP_UTF16* s,const SAP_UTF16 *format, ...)
#define sscanf_sU16_PARAMS             (s, format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(sscanf_s)    /* SCANFLIKE2 */;
END_NS_STD_C_HEADER
/* #define sscanf_sU                   SAP_UNAME_UR(sscanf_s)
 * #define sscanf_saU                  SAP_UNAME_UR(sscanf_s)
 */

/* sprintf_sU */
externC DECL_EXP int sprintf_sRFB(char * s, size_tR s1max, const char *format, ...) /* PRINTFLIKE3 */;
#define sprintf_sR                     sprintf_sRFB
#define sprintf_sU16_RETURN            intU
#define sprintf_sU16_TPARAMS           (SAP_UTF16* s, size_tU s1max,const SAP_UTF16 *format, ...)
#define sprintf_sU16_PARAMS            (s, s1max, format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(sprintf_s)   /* PRINTFLIKE3 */;
END_NS_STD_C_HEADER
#define sprintf_sU                     SAP_UNAME_UR(sprintf_s)

/* sprintf_saU() can be defined as follows, but variadic macros are a C99 feature:
 * #define sprintf_saU( s, ... )  SAP_UNAME_UR(sprintf_s)( s, sizeofU(s), __VA_ARGS__ )
 */

/*snprintf_s*/
externC DECL_EXP int snprintf_sRFB(char * s, size_tR n,const char *format, ...) /* PRINTFLIKE3 */;
#define snprintf_sR                    snprintf_sRFB
#define snprintf_sU16_RETURN           intU
#define snprintf_sU16_TPARAMS          (SAP_UTF16* s, size_tU n,const SAP_UTF16 *format, ...)
#define snprintf_sU16_PARAMS           (s, n, format, rest_args)
BEGIN_NS_STD_C_HEADER
  SAP_U16_PROTOTYPE_FLIKE(snprintf_s)    /* PRINTFLIKE3 */;
END_NS_STD_C_HEADER
#define snprintf_sU                    SAP_UNAME_UR(snprintf_s)

/*bsearch, qsort, rand */
/* void *bsearch_sRFB( const void *key, const void *base, size_t nmemb, size_t size,
 *                     int (*compar)(const void *k, const void *y, void *context),
 *                     void *context);
 * void qsort_sRFB( void *base, size_t nmemb, size_t size,
 *                  int (*compar)(const void *x, const void *y, void *context),
 *                  void *context);
 * int rand_sRFB(void);
 * #define bsearch_sR                  SECURE_NAME(bsearch_s)
 * #define qsort_sR                    SECURE_NAME(qsort_s)
 * #define rand_sR                     SECURE_NAME(rand_s)
 */

/*memcpy_s*/
externC DECL_EXP int memcpy_sRFB(void * s1, size_tR s1max, const void * s2, size_tR n);
#define memcpy_sR(  s1, s1max, s2, n ) SECURE_NAME(memcpy_s)(  s1, s1max, s2, n )
#define memcpy_saR( s1, s2, n)         SECURE_NAME(memcpy_s)(  s1, sizeofR(s1), s2, n )
externC DECL_EXP int memcpy_sU16(SAP_UTF16 * s1, size_tU s1max, const SAP_UTF16 * s2, size_tU n);
#define memcpy_sU(  s1, s1max, s2, n ) SAP_UNAME_UR(memcpy_s)(  s1, s1max, s2, n )
#define memcpy_saU(  s1,s2,n )         SAP_UNAME_UR(memcpy_s)(  s1, sizeofU(s1), s2, n )

/*memmov_s*/
externC DECL_EXP int memmove_sRFB( void * s1, size_tR s1max, const void * s2, size_tR n );
#define memmove_sR(  s1, s1max, s2, n ) SECURE_NAME(memmove_s)(  s1, s1max, s2, n )
#define memmove_saR( s1, s2, n)         SECURE_NAME(memmove_s)(  s1, sizeofR(s1), s2, n )
externC DECL_EXP int memmove_sU16(SAP_UTF16 * s1, size_tU s1max, const SAP_UTF16 * s2, size_tU n);
#define memmove_sU(  s1, s1max, s2, n ) SAP_UNAME_UR(memmove_s)( s1, s1max, s2, n )
#define memmove_saU( s1, s2, n )        SAP_UNAME_UR(memmove_s)( s1, sizeofU(s1), s2, n )

/*-----------------------------------------------------------------------------
 * sapuc.h  -   Securelib Ends here-
 *----------------------------------------------------------------------------*/

#endif /* SAPUC_H */
