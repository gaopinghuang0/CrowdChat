import crowdlib as cl, crowdlib_settings
from main import URL_PREFIX 

hit_type = cl.create_hit_type(
	title = "CrowdChat",
	description= "Please chat with requester and help them solve the proglems they have. This HIT is part of a class project at Purdue University by Gaoping Huang, Wu, Meng-Han, Jun Xiang Tee.  Feel free to email us at wu784@purdue.edu with any questions or concerns.  In case you run into any bugs, we will make sure you are paid. ",
	reward	= 1.0
)

hit = hit_type.create_hit(

	url = ("https://crowd.ecn.purdue.edu"+URL_PREFIX+"/"),
	height = 800	
	)
