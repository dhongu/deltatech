/* @(#) $Id: //bas/721_REL/src/include/sapucx.h#2 $ SAP*/

#ifndef SAPUCX_H
#define SAPUCX_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * sapucx.h: Definitions for Non-SAP RFC compiles
 *
 * Note:
 * SAP-compiles read these definitions from saptypeX.h.
 * Non-SAP-compiles do not read saptypeX.h, thus we provide
 * them here for compilations with the SAP RFC interface outside of SAP.
 * Typical use of these definitions is in sapuc.h, which defines the
 * (generic non-Unicode/Unicode) SAP U interface for RFC applications.
 */

/*
 * #defines taken from saptype.h
 */
#if defined(__cplusplus) && !defined(SAPccQC)
    #ifndef externC
      #define externC extern "C"
    #endif
    #ifndef BEGIN_externC
      #define BEGIN_externC extern "C" {
      #define END_externC }
    #endif
  #else
    #ifndef externC
      #define externC extern
    #endif
    #ifndef BEGIN_externC
      #define BEGIN_externC
      #define END_externC
    #endif
#endif

#if defined(CPP_USE_NEW_C_HEADERS)
  #define NS_STD_C_HEADER std ::
  #define BEGIN_NS_STD_C_HEADER namespace std {
  #define END_NS_STD_C_HEADER }
#else
  #define NS_STD_C_HEADER
  #define BEGIN_NS_STD_C_HEADER
  #define END_NS_STD_C_HEADER
#endif

#define CCQ_CAST(p)				/* saptypeb.h */

/*
 * switches set in saptype.h (by SAP compile):
 *
 *
 * Selection is by switch(es) set by the native compilers to indicate
 * the compilation environment.
 */
#if defined(__OS400__)
	#ifndef SAPonOS400
		#define SAPonOS400
	#endif
    #define SAPwithINT_BIGENDIAN  1
    #define SAPwithFLOAT_IEEE     1
    #if !defined(SAPwithCHAR_ASCII) && !defined(SAPwithCHAR_EBCDIC)
        #define SAPwithCHAR_EBCDIC
    #endif
#elif defined(_WIN32)
	#ifndef SAPonNT
		#define SAPonNT
	#endif
	#define SAPwithINT_LITTLEENDIAN  1
	#define SAPwithFLOAT_IEEE     1
	#define SAPwithCHAR_ASCII     1
#elif defined(__OS2__)
	#ifndef SAPonOS2_2x
		#define SAPonOS2_2x
	#endif
	#define SAPwithINT_LITTLEENDIAN  1
	#define SAPwithFLOAT_IEEE     1
	#define SAPwithCHAR_ASCII     1
#elif defined(_WINDOWS)
	#ifndef _WIN32
		#ifndef SAPonWINDOWS
			#define SAPonWINDOWS
		#endif
	#endif  /* _WIN16     */
#elif defined(__linux)
	#if !( defined(__i386__)   || defined(__ia64__)  || defined(__s390x__) || \
	       defined(__x86_64__) || defined(__PPC64__) || defined(__BYTE_ORDER__) )
		#error "sapucx.h STANDALONE on this Linux platform not yet implemented"
	#endif
	
	#if defined(__s390x__) || defined(__PPC64__) || (defined(__BYTE_ORDER__) && (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN) )
	   #define SAPwithINT_BIGENDIAN  1
	#else
	   #define SAPwithINT_LITTLEENDIAN  1
	#endif
	#ifndef SAPonLINUX
		#define SAPonLINUX
	#endif
	#ifndef SAPonLIN
		#define SAPonLIN     1
	#endif
	#ifndef SAPonUNIX
		#define SAPonUNIX    1
	#endif
	#define SAPonSYS5    1
	#define SAPonSYS5_4  1
	#define SAPwithFLOAT_IEEE        1
	#define SAPwithCHAR_ASCII        1
#if defined(__GNUC__)
	typedef double SAP_DOUBLE __attribute__ ((aligned (8)));
#else
	typedef double SAP_DOUBLE;
#endif
	#define SAP_DOUBLE_MIN  DBL_MIN
	#define SAP_DOUBLE_MAX  DBL_MAX
	#define SAP_DOUBLE_DEFINED

	#if ( defined(__ia64__)  || defined(__s390x__) || defined(__x86_64__) || \
	      defined(__PPC64__) ||                       defined(__LP64__) )
		#define SAPwith64_BIT
	#endif
#elif defined(_AIX)
	#ifndef SAPonUNIX
		#define SAPonUNIX   1
	#endif
	#define SAPonSYS5   1
	#define SAPonSYS5_2 1
	#define SAPonAIX
	#define SAPwithINT_BIGENDIAN  1
	#define SAPwithFLOAT_IEEE     1
	#define SAPwithCHAR_ASCII     1
	#if defined(__64BIT__)
		#define SAPwith64_BIT
	#endif
#elif defined(__alpha) && defined(__osf__)
	#ifndef SAPonOSF1
		#define SAPonOSF1    1
	#endif
	#ifndef SAPonUNIX
		#define SAPonUNIX    1
	#endif
	#define SAPonSYS5    1
	#define SAPonSYS5_2  1
	#define SAPwithINT_LITTLEENDIAN  1
	#define SAPwithFLOAT_IEEE        1
	#define SAPwithCHAR_ASCII        1
	#define SAPwith64_BIT			/* always. */
#elif defined(__hppa) || (defined(__hpux) && defined(__ia64))
	#ifndef SAPonUNIX
		#define SAPonUNIX
	#endif
	#ifndef SAPonHP_UX
		#define SAPonHP_UX
	#endif
	#define SAPwithINT_BIGENDIAN	1
	#define SAPwithFLOAT_IEEE	1
	#define SAPwithCHAR_ASCII	1
	#if defined(__LP64__)
		#define SAPwith64_BIT
	#endif
#elif defined(__sun)
	/* for above switches cf cc(1): -D predefinitions. */
	#ifndef SAPonSUN
		#define SAPonSUN
	#endif
	#define SAPonSYS5    1
	#define SAPonSYS5_4  1
	#ifndef SAPonUNIX
		#define SAPonUNIX    1
	#endif
	#define SAPwithCHAR_ASCII     1
	#define SAPwithFLOAT_IEEE     1
	#if defined(_BIG_ENDIAN)
		#define SAPwithINT_BIGENDIAN  1
	#else
		#define SAPwithINT_LITTLEENDIAN  1
	#endif
	#if defined (_LP64)
		#define SAPwith64_BIT
	#endif

#elif defined(__MVS__)
	#ifndef SAPonUNIX
		#define SAPonUNIX    1
	#endif
	#define SAPonSYS5    1
	#define SAPonMVSOE   1
	#define SAPonOS390   1
	#define SAPwithINT_BIGENDIAN 1
	#define SAPwithFLOAT_IEEE    1
	#if __STRING_CODE_SET__==ISO8859-1
	  #define SAPwithCHAR_ASCII    1
	#else
          #define SAPwithCHAR_EBCDIC   1
	#endif
	#if defined(_LP64)
		#define SAPwith64_BIT
	#endif
#elif defined(sinix)
	/* for above switch cf cc(1) */
	#ifndef SAPonRM600
		#define SAPonRM600
	#endif
	#ifndef SAPonUNIX
		#define SAPonUNIX    1
	#endif
	#define SAPonSYS5    1
	#define SAPonSYS5_2  1
	#define SAPonSYS5_4  1
	#define SAPonSINIX   1
	#define SAPonSINIX5_42   1
	#define SAPwithINT_BIGENDIAN  1
	#define SAPwithFLOAT_IEEE     1
	#define SAPwithCHAR_ASCII     1
	#if defined(__LP64__)
		#define SAPwith64_BIT
	#endif
#elif defined(__APPLE__)

    #define SAPonDARWIN   1
	#ifndef SAPonUNIX
    	#define SAPonUNIX     1
    #endif
	#ifndef SAPonDARW
    	#define SAPonDARW     1
    #endif

    #define SAPwithFLOAT_IEEE     1
    #define SAPwithCHAR_ASCII     1

	#if defined __x86_64__
        #define SAPwithINT_LITTLEENDIAN  1
        #define SAPwith64_BIT
	#elif defined __i386__
        #define SAPwithINT_LITTLEENDIAN  1
		#define SAPonBSD      1
	#else
		#define SAPwithINT_BIGENDIAN  1
		#define SAPonBSD      1
	#endif

#else
	#error "sapucx.h STANDALONE not yet implemented"
#endif


/* Some function pointers declared in sapuc.h (example: toupperU())
 * need __declspec(dllimport) on Windows, because they will be
 * imported from libsapucum.dll
 */
#if defined(SAPonNT)
  #define __SAP_DLL_DECLSPEC __declspec(dllimport)
#else
  #define __SAP_DLL_DECLSPEC
#endif


/*
 * Non-SAP compile: Types
 * (See saptypeb.h)
 */
/*
 * SAP_CHAR
 * SAP_UC
 */

#ifdef SAPonAIX
  #if defined(_AIX51) && defined(SAPwith64_BIT)
    #define SAPonAIX_wchar_is_4B
  #else
    #define SAPonAIX_wchar_is_2B
  #endif
#endif

#ifdef SAPonAIX
  #if defined(_AIX51) && defined(SAPwith64_BIT)
    #define SAPonAIX_wchar_is_4B
  #elif defined(SAPccQ)
    #define SAPonAIX_wchar_is_4B
  #else
    #define SAPonAIX_wchar_is_2B
  #endif
#endif

#if defined(SAPonNT)      || \
    defined(SAPonOS400)   || \
   (defined(SAPonOS390) && !defined(_LP64))  || \
    defined(SAPonAIX) && defined(SAPonAIX_wchar_is_2B)
  #define WCHAR_is_2B
#else
  #define WCHAR_is_4B
#endif

#if defined(SAPonLIN) && defined(GCC_UTF16_PATCH)
  #if __GNUC_PREREQ (4,3)
    #include <uchar.h>
    #define SAP_UC_is_char16
  #endif
#endif

/* Starting with z/OS release 1.11 the compiler supports UTF-16 */
/* and UTF-32 strings and literals similar to Linux             */
/* UTF-16 characters representing Unicode are of type char16_t  */

#if defined(SAPonOS390) && defined(_LP64) && (__COMPILER_VER__ >= 0x410B0000)
  /* for C++ the compile option KEYWORD(char16_t,char32_t) */
  /* makes including of uchar.h surplus                    */
  #ifndef __cplusplus
    #include <uchar.h>
  #endif
  #define SAP_UC_is_char16
#endif

#ifndef SAPwithUNICODE
  #define SAP_UC_is_1B
  typedef char SAP_CHAR;
  typedef char SAP_UC;
#else  /* SAPwithUNICODE */
  #if defined(WCHAR_is_2B)
    #define SAP_UC_is_wchar
    typedef wchar_t SAP_CHAR;
    typedef wchar_t SAP_UC;
  #elif defined(SAP_UC_is_char16)
    typedef char16_t SAP_CHAR;
    typedef char16_t SAP_UC;
  #else
    #define SAP_UC_is_UTF16_without_wchar
    typedef unsigned short SAP_CHAR;
    typedef unsigned short SAP_UC;
  #endif
#endif /* SAPwithUNICODE or not */

/*
 * RFCSDKwith(out)UTF16_LITERALS
 * for RFC SDK applications: controls use of UTF-16
 * literal enabled compilers.
 */
#if defined(RFCSDKwithUTF16_LITERALS)
#elif defined(RFCSDKwithoutUTF16_LITERALS)
  #define SAPwithoutUTF16_LITERALS
#elif defined(WCHAR_is_2B) || \
    defined(SAPonHP_UX) || \
    (defined(SAPonLIN) && defined(__i386__) && defined(__GNUC__) && (__GNUC__<3)) || \
    (defined(SAPonLIN) && defined(GCC_UTF16_PATCH)) || \
    defined(SAPonSUN) || defined(SAPonAIX) || \
    (defined(SAPonOS390) && (__COMPILER_VER__ >= 0x410B0000))
  /* we have literals for UTF-16 */
#else
  #define SAPwithoutUTF16_LITERALS
#endif



/*
 * General Headers:			
 *
 * defines required by sapuc.h included next.
 * Note:
 * Some of these declarations may be unused in Unicode mode,
 * others (e.g. memcpy) may be used to implement U functions
 * (e.g. memcpyU) in Unicode mode.
 */
#include <stddef.h>		/* saptypeb.h. size_t */
#include <stdio.h>		/* saptypeb.h. FILE */
#include <ctype.h>		/* is...() */
#include <string.h>		/* str...() mem...() */

/*
 * SAP_RAW
 * SAP_SRAW
 * SAP_USHORT
 */
typedef unsigned char	SAP_RAW;
typedef signed char	    SAP_SRAW;
typedef unsigned short	SAP_USHORT;
/*
 * Numeric Types:
 */
#include <limits.h>	/* need _MAX values to define numeric types: */
#if UINT_MAX == 0xFFFFFFFFu
	typedef unsigned int SAP_UINT;
#elif ULONG_MAX == 0xFFFFFFFFu
	typedef unsigned long SAP_UINT;
#else
	#error "We need an unsigned int type with 4 bytes"
#endif
#if INT_MAX == 0x7FFFFFFF
	typedef int SAP_INT;
#elif LONG_MAX == 0x7FFFFFFF
	typedef long SAP_INT;
#else
	#error "We need an int type with 4 bytes"
#endif
/*
 * SAP_SHORT:
 */
#if SHRT_MAX == 0x7FFF
  typedef short SAP_SHORT;       /* Value range: SHRT_MIN .. SHRT_MAX */
  #define SAP_SHORT_MIN  SHRT_MIN
  #define SAP_SHORT_MAX  SHRT_MAX
#else
  #error "We need a short type with 2 bytes"
#endif
#define SAP_SHORT_BYTES  2

/**********************************************************************/
/* SAP_BOOL:   boolean value (TRUE or FALSE)                          */
/**********************************************************************/
#ifdef SAP_BOOL_ENUM
  typedef enum { FALSE = 0, TRUE = 1 } SAP_BOOL;
#else
  typedef unsigned char SAP_BOOL;
  #ifndef FALSE
    #define FALSE  0
  #endif

  #ifndef TRUE
    #define TRUE  1
  #endif
#endif

/* ts: on AS/400, SAP_BOOL must be char, only char is guaranteed to be the
 * same size on ILE and PASE */
#if ( defined(SAPonOS400) || defined(SAPwithPASE400) ) && defined(SAP_BOOL_ENUM)
#error SAP_BOOL must be char on iSeries, do not define SAP_BOOL_ENUM
#endif


/*
 * SAP_DOUBLE:
 */
#ifndef SAP_DOUBLE_DEFINED
#define SAP_DOUBLE_DEFINED
  typedef double SAP_DOUBLE;          /* Value range is at least        */
                                      /* +- 10**37, 15 digits precision */
  #define SAP_DOUBLE_MIN  DBL_MIN
  #define SAP_DOUBLE_MAX  DBL_MAX
#endif

/**********************************************************************/
/* LINE_USING_PROC                                                    */
/* The type for generalized dump routines:                            */
/*   a pointer to a procedure, which will be called for (and with)    */
/*   every line, that shall be output. The parameters of each such    */
/*   procedure must be:                                               */
/*   1st: address of text data.                                       */
/*   2nd: length of that data. Counted in number of basic characters. */
/**********************************************************************/
typedef void (* LINE_USING_PROC) (SAP_CHAR *  buffer,
                                  int         number_of_chars );
/**********************************************************************/
/* C standard types                                                   */
/* classified if they count character length or byte length           */
/**********************************************************************/
/*SAPUNICODEOK_CHARLEN*/ typedef int             intU;
/*SAPUNICODEOK_RAWLEN*/  typedef int             intR;
/*SAPUNICODEOK_CHARLEN*/ typedef unsigned int    unsigned_intU;
/*SAPUNICODEOK_RAWLEN*/  typedef unsigned int    unsigned_intR;
/*SAPUNICODEOK_CHARLEN*/ typedef short           shortU;
/*SAPUNICODEOK_RAWLEN*/  typedef short           shortR;
/*SAPUNICODEOK_CHARLEN*/ typedef unsigned short  unsigned_shortU;
/*SAPUNICODEOK_RAWLEN*/  typedef unsigned short  unsigned_shortR;
/*SAPUNICODEOK_CHARLEN*/ typedef long            longU;
/*SAPUNICODEOK_RAWLEN*/  typedef long            longR;
/*SAPUNICODEOK_CHARLEN*/ typedef unsigned long   unsigned_longU;
/*SAPUNICODEOK_RAWLEN*/  typedef unsigned long   unsigned_longR;
/*SAPUNICODEOK_CHARLEN*/ typedef size_t          size_tU;
/*SAPUNICODEOK_RAWLEN*/  typedef size_t          size_tR;


/*
 * SAP_DATE					(saptypeb.h)
 * SAP_TIME
 * SAP_BCD
 */
/* date: YYYYMMDD */
#define SAP_DATE_LN 8
typedef SAP_CHAR  SAP_DATE [SAP_DATE_LN];

/* time: HHMMSS */
#define SAP_TIME_LN 6
typedef SAP_CHAR  SAP_TIME [SAP_TIME_LN];

/* BCD numbers */
typedef SAP_RAW   SAP_BCD;


/*
 * SAP_UUID                                        (saptypec.h)
 */
#ifndef SAP_UUID_TYPEDEFD
#define SAP_UUID_TYPEDEFD
typedef struct SAP_UUID
{
    SAP_UINT   a;
    SAP_USHORT b;
    SAP_USHORT c;
    SAP_RAW    d[8];
}
SAP_UUID;
#endif

#ifndef __midl

#if defined (SAPonHPPA)
  /* saptype.h */
  /**********************************************************************/
  /*                                                                    */
  /*  IA64 generally needs 16 byte alignment for the spilled floating   */
  /*  point registers in structures like jmp_buf and ucontext_t.        */
  /*                                                                    */
  /*  Intel's IA64 ABI specifies 'long double' to be 16 byte for LP64.  */
  /*                                                                    */
  /*  Conventions:                                                      */
  /*    see saptypeb.h                                                  */
  /*                                                                    */
  /**********************************************************************/
  #ifdef SAPonHPIA64
    #define PLATFORM_MAX_T platform_max_t
    typedef long double platform_max_t;
  #endif

#elif defined (SAPonLIN)
  /**********************************************************************/
  /*                                                                    */
  /*  IA64 generally needs 16 byte alignment for the spilled floating   */
  /*  point registers in structures like jmp_buf and ucontext_t.        */
  /*                                                                    */
  /*  Intel's IA64 ABI specifies 'long double' to be 16 byte for LP64.  */
  /*                                                                    */
  /*  Conventions:                                                      */
  /*    see saptypeb.h                                                  */
  /*                                                                    */
  /**********************************************************************/
  #if defined(__ia64__)
    #define PLATFORM_MAX_T platform_max_t
    typedef long double platform_max_t;
  #else
    #define PLATFORM_MAX_T SAP_DOUBLE
  #endif

#elif defined (SAPonNT)
  /**********************************************************************/
  /*                                                                    */
  /*  IA64 generally needs 16 byte alignment for the spilled floating   */
  /*  point registers in structures like jmp_buf and ucontext_t.        */
  /*                                                                    */
  /*  There's no 16 byte fundamental type on NT so we align an array.   */
  /*                                                                    */
  /*  Conventions:                                                      */
  /*    see saptypeb.h                                                  */
  /*                                                                    */
  /**********************************************************************/
  #if defined(_M_IA64) || defined(_M_AMD64)
    #define PLATFORM_MAX_T platform_max_t
    /* typedef __declspec(align(16)) char platform_max_t[16];*/
    typedef __declspec(align(16)) SAP_SRAW platform_max_t[16];
  #endif
  
#elif defined (SAPonRS6000)
   /********************************************************************/
   /* define 16 byte alignment on rs6000                               */
   /********************************************************************/
   #define PLATFORM_MAX_T platform_max_t
   typedef struct{ char d[16]; } __attribute__((aligned(16))) platform_max_t;
  
#endif

  /* SAP_MAX_ALIGN_T from saptypeb.h */
/**********************************************************************/
/*                                                                    */
/* SAP_MAX_ALIGN_T:                                                   */
/* structure with maximum possible size, used for alignment           */
/*                                                                    */
/* SAP_MAX_ALIGN:                                                     */
/* maximum alignment required for any integral data type              */
/*                                                                    */
/* If a certain platform contains a type that exceeds the size of     */
/* the C-defined integral data types, define PLATFORM_MAX_T in the    */
/* platform dependent part of saptype.h                               */
/*                                                                    */
/* Example: (in saptype.h)                                            */
/*                                                                    */
/* #ifdef SAPon<platform>                                             */
/* union                                                              */
/* {                                                                  */
/*   longlong my_largest_type;                                        */
/* } PLATFORM_MAX_T                                                   */
/* #endif                                                             */
/*                                                                    */
/**********************************************************************/
#ifndef SAP_MAX_ALIGN_T_DEFINED
#define SAP_MAX_ALIGN_T_DEFINED

#ifndef PLATFORM_MAX_T
typedef void * PLATFORM_MAX_T;
#endif

typedef union
{
  long               align_1;
  double             align_2;
  void *             align_3;
  PLATFORM_MAX_T     align_4;
} SAP_MAX_ALIGN_T;
#endif /*SAP_MAX_ALIGN_T_DEFINED*/

/**********************************************************************/
/* IEEE 754r decimal floating point types                             */
/* DecFloat16 and DecFloat34                                          */
/* See sapdecf.h for more details                                     */
/**********************************************************************/
#ifndef SAP_DecFloat_DEFINED
#define SAP_DecFloat_DEFINED

/* ABAP kernel representation of the IEEE 754r decimal floating point 
   type with 64 bits. */
typedef union
{
  SAP_RAW    bytes[8];
  SAP_DOUBLE align;
} DecFloat16;

/* ABAP kernel representation of the IEEE 754r decimal floating point 
   type with 128 bits. */
typedef union
{
  SAP_RAW         bytes[16];
  SAP_MAX_ALIGN_T align;
} DecFloat34;


/* Length definition for the binary sortable decimal floating point types */
enum DecFloatRawLen{ 
	 /* Length of binary sortable IEEE 754r 64-bit variant in bytes. */ 
	DecFloat16RawLen = 8, 
	 /* Length of binary sortable IEEE 754r 128-bit variant in bytes. */ 
	DecFloat34RawLen = 16 
};

/* Binary sortable variant of the IEEE 754r with 64-bits. */
typedef SAP_RAW DecFloat16Raw [DecFloat16RawLen];
/* Binary sortable variant of the IEEE 754r with 128-bits. */
typedef SAP_RAW DecFloat34Raw [DecFloat34RawLen];

/* Length definition for ABAP kernel representation of the IEEE 754r 
   decimal floating point types */
enum DecFloatLen   { 
	/*  Length of the IEEE 754r 64-bit type in bytes. */ 
	DecFloat16Len    = 8,  
  /* Length of the IEEE 754r 128-bit type in bytes. */ 
  DecFloat34Len    = 16 
};

#define DECF_16_MAX_STRLEN 25   /* maximum string length, +1 */ 
#define DECF_34_MAX_STRLEN 43  /* maximum string length, +1 */ 

/* String buffer type for DecFloat34 numeric strings. */
typedef SAP_UC DecFloat34Buff [DECF_34_MAX_STRLEN]; 
/* String buffer type for DecFloat16 numeric strings. */
typedef SAP_UC DecFloat16Buff [DECF_16_MAX_STRLEN]; 
#endif /*SAP_DecFloat_DEFINED*/

#endif /* __midl */

#ifdef __cplusplus
}
#endif

#endif /* SAPUCX_H */
