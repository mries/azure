t=0
s=15
while [ $t -le $s ]; do
       #iotop -otbn1>>test-out
       iotop -otbn1|egrep -iv "read|write" |awk '{print  "IO: "$11$12";  "$13";  "$15}'>>test-out

           t=$(( $t + 1 ))
echo "Time left in seconds:" $(($s-$t))


    sleep 1
done
