## 18.0.1.1.5 (2026-11-27)

- A barcode that is not a valid EAN-13 is printed on the label as it is, in Code128. It was
  drawn as EAN-13, which recomputes the last digit: an internal code with a wrong check digit
  came out as a different code, sometimes another product's (5555500000372 printed as
  5555500000371), and a code with letters stopped the report.
