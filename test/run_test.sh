#!/bin/bash

./audio_srv.py &
audio_srv_pid=`echo $!`

./html_srv.py &
html_srv_pid=`echo $!`

close_srv()
{
    kill -9 ${audio_srv_pid} ${html_srv_pid}
}

trap 'close_srv' SIGINT

wait


