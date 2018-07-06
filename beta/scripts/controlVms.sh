function help () {
	        echo "  restart - restart vme(not used)"
		echo "  stopvm - stop vm"
		 echo "  listimages - list images"
		 echo "  listrunning - List running VMs"
		 echo "  listvms  - List all vms"
		 echo "  -h This help"
		exit
	}

function restart()
	{
		echo restart
}
function stop()
	{
		echo stop
}
function start()
	{
		echo start
}
function images()
	{
		echo images
		printf '%s ' 'Select a type of image, e.g. rhel:'
		read offer
		az vm image list --offer $offer --all --output table
#		printf ' %s ' ' Would you like to exit or continue on to create a vm, (yes\no)? ' &read answer;
		#	if [[  "$answer" == "no" ]]; then
		#		exit 1
		#	elif [[ "$answer" == "yes" ]]; then
		#		create
		#	fi
		printf 'Would you like to create a vm? : (yes or no):' &read answer
			if [[  $answer == "no" ]]; then
				exit 1
			elif [[ $answer == "yes" ]]; then
				create
			fi
}
function create()
	{
		echo create
}
function listRunning()
	{
		echo list running
}
function listVms()
{	
		echo list all vms
		 az vm list -d --output table
}
#	while getopts "restart:stopvm:startvm:listimages:createvms:listrunning:listvms:h" opt;
#		do
printf '%s' 'wWhat would you like to "do"?'
echo "restart(restartvm), stop(stopvm), start vm(startvm); list all images images(listimages); create vm(createvm);" 
echo "list running vms(listrunning); list all vms(listvms); help(help/h:)" &read  selection;

		         case "$selection" in
                              restart) restart;;
	                      stop|stopvm) stop;;
	                      start|startvm ) start;;
	                      list|listimages) images;;
	                      create|createvm ) create;;
	                      running|listrunning ) listRunning;;
			      listvms ) listVms;;
			      help|h) help && echo help;;
			  esac
		
echo $opt	
		#az vm image list --offer $OFFER --all --output table

