echo " 'execute' to run cpu checker, 'stop' to stop run existing process:" & read answer
         

             if [[ "$answer" == "execute" ]]; then          
                echo execute
             elif [[ "$answer" == "stop" ]]; then 
                  echo stop script
          
             elif  [[  "$answer" != "execute" || "$answer" != "stop" || -z "$answer" ]]; then
                  echo You must select execute or stop
             fi
