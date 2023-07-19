DB_type = "plaintext"#"plaintext" or "mondoDB"


if DB_type == "plaintext":
	import database
elif DB_type == "mondoDB": #not yet implemented
	import database #hue
else:
	import sys
	print("Unsupported database type \"%s\"" % DB_type)
	sys.exit()