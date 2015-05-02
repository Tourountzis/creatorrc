#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Contact: hephaestos@riseup.net - 8764 EF6F D5C1 7838 8D10 E061 CF84 9CE5 42D0 B12B


# Five eye countries and Israel
FIVE_EYES_I = ['us','ca','gb','nz','au','il']

# America and their guards
AMERICA_S = ['ar','bo','br','cl','co','ec','gf','gy','py','pe','sr','uy','ve']
AMERICA_C = ['mx','cu','ht','dm','jm','pa','gt','hn','ni','cr','bs','bz']
AMERICA_TARGETS = AMERICA_S + ['pt','es','za','lr'] 

# Maghreb countries and close european countries as guards
MAGHREB = ['ml', 'mr', 'eh', 'ma', 'dz', 'tn', 'ly']
MAGHREB_TARGETS = ['pt','es','fr','it','gr']

# South east asia.
SEA = ['jp', 'kr', 'tw', 'hk', 'sg', 'vn']

# European peninsula countries
EUROPEAN_TARGETS = MAGHREB_TARGETS + ['de','nl','ch','se', 'dk','be','lu','at','cz','pl','ro','lv', 'ee','lt','no','ua','ru','si','sk','hr','rs','bg', 'hu', 'fi','md','pl']

# Basically all countries with relays, omitting FIVE_EYES_I
OTHERS_TARGETS = EUROPEAN_TARGETS + AMERICA_S + SEA

# Profiles for larger Tor countries:
guard_resolver = dict([
	( 'de' , ['de', 'nl', 'ch', 'pl', 'dk'] ),
	( 'ch' , ['ch', 'de', 'fr','it','at'] ),
	( 'at' , ['at','it','ch','de','cz','hu','si','sk'] ),
	( 'cz' , ['cz','de','pl','at','sk'] ),
	( 'pl' , ['pl', 'de', 'cz','si','ua'] ),
	( 'dk' , ['dk','de','se','no','is'] ),
	( 'se' , ['se', 'no', 'dk','fi','is'] ),
	( 'nl' , ['nl', 'be','de','lu','fr'] ),
	( 'be' , ['be', 'fr', 'nl', 'lu','de'] ),
	( 'lu' , ['lu','nl','be','fr','de'] ),
	( 'fr' , ['fr', 'es','ch','be'] ),
	( 'gb' , ['gb', 'ie', 'fr','be','nl'] ),
	( 'us' , ['us', 'ca'] ),
	( 'ca' , ['ca', 'us'] ),
	( 'il' , ['il', 'tr', 'gr', 'it', 'ro','ua','ru'] ),
	( 'au' , ['au', 'nz'] + SEA ),
	( 'nz' , ['au', 'nz'] + SEA ),
	( 'ro' , ['ro','md','ua','tr','hu'] ),
	( 'ru' , ['ru', 'lv', 'ee', 'lt', 'ua'] ),
	( 'lv' , ['ru', 'lv', 'ee', 'lt'] ),	
	( 'ee' , ['ru', 'lv', 'ee', 'lt'] ),	
	( 'lt' , ['ru', 'lv', 'ee', 'lt'] ),
	( 'it' , ['it','fr','gr','ch','at','hr','si'] ),
	( 'ua' , ['ua', 'ro', 'md','pl','ru'] ),
	( 'md' , ['ua', 'ro', 'md'] ),
	( 'gr' , ['gr', 'it', 'tr', 'hr', 'ro'] ),
	( 'pt' , ['pt', 'es', 'fr'] ),
	( 'es' , ['pt', 'es', 'fr'] ),
	( 'tr' , ['tr', 'gr', 'it', 'ro','ua','ru'] ),
	( 'hu' , ['hu', 'at', 'cz', 'pt', 'ro'] ),
	( 'is' , ['is', 'dk','no','se'] ),
	( 'no' , ['no', 'dk','se','is'] ),
	( 'africa' , EUROPEAN_TARGETS + ['za','lr'] ),
	( 'southasia' , SEA ),
	( 'south-asia' , SEA ),
	( 'america' , AMERICA_TARGETS ),
	( 'europe' , EUROPEAN_TARGETS ),
	( 'other' , OTHERS_TARGETS )
	])

#
# Regions that guard each other:
#
for country in SEA:
	guard_resolver[country] = SEA

for country in AMERICA_S:
	guard_resolver[country] = AMERICA_TARGETS
	
for country in AMERICA_C:
	guard_resolver[country] = AMERICA_TARGETS + [country]

for country in MAGHREB:
	guard_resolver[country] = MAGHREB_TARGETS + [country]


def guards_close_to_home(resolver=guard_resolver):
	country_code = input("\nWhat is your two letter country code?\n").lower()
	if country_code in resolver:
		return resolver[country_code], country_code
	else:
		print( "\nCountry code '" + country_code + "' not known." )
		print( "Try other code or one of the general regions:" )
		print( "africa, southasia, america, europe, other" )
		return guards_close_to_home(resolver)
	
if __name__=="__main__":
	# This is used only during development
	print( resolve_guard() )
	
