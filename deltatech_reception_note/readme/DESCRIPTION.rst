Features:
 - Creates new types of RFQ's: "RFQ only" and "Reception note"
 - RFQ only types cannot be validated, they can only be sent to the supplier
 - Reception note types can be validated, they decrement the quantities found in RFQ only types from the same supplier (until 0 qty remains). If not enough quantities found on RFQ's, an error is displayed. The quantity errors can be ignored by checking the "Ignore quantities" checkbox. A message wil be logged if any found
