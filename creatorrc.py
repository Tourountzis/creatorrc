from guard_country_resolver import guards_close_to_home, FIVE_EYES_I

def download_descriptors():
	from stem.descriptor.remote import DescriptorDownloader
	print( "Fetching server descriptors..." )
	return DescriptorDownloader().get_server_descriptors().run()
	
def questionable_relays(relays=None):
	# Questionable relays are those that:
	# - Don't run a recent version of Tor.
	# - Run on win. xp.
	if relays == None:
		relays = download_descriptors()
	old = [ r.fingerprint for r in relays if r.tor_version and r.tor_version.micro < 4 and r.tor_version.minor < 3 ]
	winxp = [ r.fingerprint for r in relays if r.operating_system and 'Windows XP' in r.operating_system ]
	return set(old + winxp)

def sector():
	# This option is designed for security.
	# Use nearby guards and try to avoid certain territories.
	questionables = questionable_relays()
	guards, client_country = guards_close_to_home()
		
	torrc = "\n\n# Strictly exclude all circuits that do not match our preferences.\n"
	torrc += "# This WILL prevent connectivity to some hidden services.\n"
	torrc += "# Turning off StrictNodes wouldn't be terrible,\n"
	torrc += "# mostly used when connecting to hidden services\n"
	torrc += "# If you prefer not to be strict, change following line to 'StrictNodes 0'\n"
	torrc += "StrictNodes 1\n\n"
	
	torrc += "# Exclude 5 eyes countries + Israel.\n"
	torrc += "# Also exclude questionable relays.\n"
	torrc += "ExcludeNodes BadExit"
	for country in set(FIVE_EYES_I) - set(guards):
		torrc += ", {" + country + "}"
	for fp in questionables:
		torrc += ", " + fp
	
	torrc += "\n\n# Only use entry nodes from your region.\n"
	torrc += "# Your own region can already see you connecting.\n"
	torrc += "# No reason for a Rio client to connect to Moskow guard.\n"
	torrc += "EntryNodes {" + guards.pop() + "}"
	for country in guards:
		torrc += ", {" + country + "}"
	
	if client_country in FIVE_EYES_I:
		exit_exclude = set(FIVE_EYES_I).intersection(set(guards))
		torrc += "\n\n# Your country is specifically excluded for exits, but guards are still allowed.\n"
		torrc += "# Other five eyes and israel are already excluded.\n"
		torrc += "ExcludeExitNodes {" + exit_exclude.pop() + "}"
		for country in exit_exclude:
			torrc += ", {" + country + "}"
			
	torrc += "\n\n# Avoid disk writes, are there any drawbacks to this?\n"
	torrc += "AvoidDiskWrites 1\n\n"
	
	return torrc

def evator():
	# This option is designed to avoid captcha's
	relays = download_descriptors()
	
	# Select all exits:
	relays = [ relay for relay in relays if relay.exit_policy and relay.exit_policy.is_exiting_allowed() ]
	
	# Define speed limits in bytes per second.
	# This corresponds to a 100 - 300 kB/s range.
	# The minimum is just set to exclude nodes that are horribly slow.
	min_speed = 100000
	max_speed = 300000
	
	# Select relays with the appropriate speed range
	relays = [ r for r in relays if r.average_bandwidth > min_speed and r.average_bandwidth < max_speed ]
	
	# Finally retrieve fingerprints of selected relays.
	fingerprints = [ relay.fingerprint for relay in relays ]
	
	# Create the torrc for this configuration
	torrc = "\n\n# Select these nodes as exits\n"
	torrc += "ExitNodes " + fingerprints.pop()
	for exit in fingerprints:
		torrc += ", " + exit
	
	torrc += "\n\n"
	return torrc
	
def speetor():
	# Torrc to have high throughput.
	# This is something that the project advises against.
	# It is advised against because high throughput is bad for anonymity and also hurts the network.
	relays = download_descriptors()
	
	# The sort that we use in this function, returns only the fingerprints
	sort = lambda x : [ y[1] for y in sorted(x, key = lambda x : x[0], reverse=True) ]
		
	# Fortran style, where are the exits? 
	exit_or_not = [r.exit_policy.is_exiting_allowed() for r in relays]
	
	# Select 1000 fastest non-exits as guards
	guards = sort([ (r[0].average_bandwidth, r[0].fingerprint)  for r in zip(relays, exit_or_not) if not r[1]] )[:1000]
	
	# Select 1000 fastest exits as exits
	exits = sort([ (r[0].average_bandwidth, r[0].fingerprint)  for r in zip(relays, exit_or_not) if r[1]] )[:1000]
	
	# Select 4000 slowest relays to exclode from everywhere in the circuit. (selects middle relay)
	excludes = sort([ (r.average_bandwidth, r.fingerprint)  for r in relays ])[-4000:]
	
	assert len(exits) == 1000, "Error selecting exits"
	assert len(guards) == 1000, "Error selecting guards"
	assert len(excludes) == 4000, "Error selecting relays to exclude"
	
	torrc = "\n\n# Only use the 1000 fastest guards\n"
	torrc += "EntryNodes " + guards.pop()
	for guard in guards:
		torrc += ", " + guard
	
	torrc += "\n\n# Exclude the 4000 slowest relays\n"
	torrc += "ExcludeNodes " + excludes.pop()
	for exclude in excludes:
		torrc += ", " + exclude
	
	torrc += "\n\n# Only use the 1000 fastest exits\n"
	torrc += "ExitNodes " + exits.pop()
	for exit in exits:
		torrc += ", " + exit
	
	torrc += "\n\n"
	return torrc
	
def notor(MAX_AGE=None, relays=None):
	def age(relay, now):
		# Returns age of relay in seconds compared to 'now'.
		ti, t = relay[2].split(" ")
		date = (int(ti.split("-")[0]), int(ti.split("-")[1]), int(ti.split("-")[2]), int(t.split(":")[0]), int(t.split(":")[1]), int(t.split(":")[2]))

		return (now - datetime.datetime(*date)).total_seconds()
		
	def download_relay_ages():
		import urllib.request
		import json
		
		proxy = urllib.request.ProxyHandler({'https': '127.0.0.1:8118', 'http': '127.0.0.1:8118'})
		opener = urllib.request.build_opener(proxy)
		urllib.request.install_opener(opener)
		
		url = 'https://onionoo.torproject.org/details' 
		obj = json.loads(urllib.request.urlopen(url).readall().decode('utf-8'))
		return [ (r['fingerprint'], r['country'], r['first_seen']) for r in obj['relays'] if 'Exit' in r['flags']]
		
	# noTor, select exits that are very new in the tor consensus.
	# This should make it less obvious that the connection comes from tor at the time of use.
	import datetime
	
	# Time increment in seconds for selecting most recent relays.
	AGE_DELTA = 60*60*4
	
	# If not in recursion:
	if relays == None:
		# Set max_age in seconds
		MAX_AGE = AGE_DELTA
		# Get extra server descriptors and extra-info descriptors to discover relay age
		print( "Downloading relay list..." )
		relays = download_relay_ages()
	
	now = datetime.datetime.now()
	
	new_exits = [ r[0] for r in relays if age(r,now) < MAX_AGE ]
	
	if len(new_exits) == 0:
		# Recursion to get some exits.
		return notor(MAX_AGE + AGE_DELTA, relays)
	else:
		# Create the torrc for this configuration
		torrc = "\n\n# Select these nodes as exits\n"
		torrc += "ExitNodes " + new_exits.pop()
		for exit in new_exits:
			torrc += ", " + exit
		torrc += "\n\n"
		return torrc	
	 

def help():
	end = '\033[0m'
	ul = lambda x : '\033[4m' + x + end # underline text
	red = lambda x : '\033[91m' + x + end # red text
	print( "\nCreate a tor configuration that reflects your preference." )
	print( "Select one of the following options:\n")
	print( "--sector\tSecure tor configuration." )
	print( "--speetor\tIf speed is what you need." )
	print( "--evator\tFor evading captchas." )
	print( "--notor\t\tAccess sites that block tor." )
	print( "--help\t\tShow this helpful message.\n" )
	
	msg = ul("SecTor") + " is " + red("NOT RECOMMENDED") + " by the torproject (torproject.org)." 
	msg += " It is designed to improve upon the default tor configuration in terms of security.\n"
	msg += "SecTor does three things:\n"
	msg += "1. Select guards that are in your region, so that not the entire world sees you taking a first hop.\n" 
	msg += "2. As much as possible it avoids routing through the five eyes countries (us, ca, gb, au, nz) and Israel.\n" 
	msg += "3. It excludes questionable relays, which run Windows XP or an outdated version of tor.\n"
	print( msg )
	
	msg = ul("SpeeTor") + " configures tor to only use fast nodes."
	msg += " This can be usefull for sharing large files quickly over tor, but is bad for anonymity and the tor network.\n"
	print( msg )
	
	msg = ul("EvaTor") + " selects slow nodes, which are used by less users."
	msg += " This means that the chance of having to fill out a captcha is significantly reduced.\n"
	print( msg )
	
	msg = ul("noTor") + " tries to make it possible to access websites and services that attempt to block tor."
	msg += " This is done by only selecting very new exit relays."
	msg += " Hopefully the newer relays have not been added to a block list yet."
	msg += " The use of tor to access the website or service DOES become evident within a short period after the fact."
	msg += " " + ul("The noTor configuration should be updated at least daily for it to work.\n")
	print( msg )
	
	print( ul("Warnings:") )
	msg = "1. Using speeTor, evaTor and noTor instead of the tor defaults " + red("REDUCES YOUR ANONYMITY")
	msg += ", but you might prefer it if you are not concerned with strong adversaries."
	msg += " In particular, notor is very vulnerable."
	msg += " However, if you expect no strong adversaries or merely use Tor for circumvention, you should be fine.\n"
	msg += "2. SecTor is designed to be more secure than default tor, especially against powerful adversaries."
	msg += " However, secTor is " + red(ul("POTENTIALLY LESS SECURE")) + " than using tor defaults.\n"
	msg += "3. Use is at YOUR own risk.\n"
	print( msg )
	
	import sys
	sys.exit(0)

if __name__=="__main__":
	import sys
	
	args = sys.argv[1:]
		
	# Check if all command line arguments are understood
	if len(args) == 0:
		help()
	if len(args) > 1:
		print("\nCan only handle one argument at a time.")
		help()
		
	arg = args[0]
	if arg not in set(['-h','--help','--sector','--speetor','--evator','--notor']):
		print("\nOption not understood, showing help instead:")
		help()
	
	if arg in ['-h','--help']:
		help()
	
	arg_resolver = dict([ ('--sector', sector), ('--speetor', speetor), ('--evator', evator), ('--notor', notor) ])
	torrc = arg_resolver[arg]()
	
	f = open("tor_config.txt", "w")
	f.write(torrc)
	f.close()
	
	print( "Done!" )
	print( "Torrc saved in tor_config.txt" )
	
	
	
