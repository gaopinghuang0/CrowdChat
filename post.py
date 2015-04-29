import crowdlib as cl, crowdlib_settings
from main import URL_PREFIX 

hit_type = cl.create_hit_type(
	title = "Find real need before shopping (bonus)",
	description= "Please chat with requester and help to clarify his/her real need before purchasing certain merchandise.",
	reward	= 0.4
)

hit = hit_type.create_hit(

	url = ("https://crowd.ecn.purdue.edu"+URL_PREFIX+"/"),
	height = 800	
	)
