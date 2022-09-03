/*
    Functions for interacting with the server to scan for stations, tune, etc.

    Much help from https://stackoverflow.com/a/22577506
*/

// TODO: Figure out playback of audio when this is called (e.g. when paused),
//       as currently doing so is very glitchy...
function webRadioTune(url, navLink)
{
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function()
    {
        if (this.readyState == 4)
        {
            if (this.status == 204)
            {
                stationListUpdateSelection(navLink, true);
            }
            else
            {
                stationListUpdateSelection(navLink, false);
            }
        }
    };
    xhttp.open("PATCH", url, true);
    xhttp.send();
}

function webRadioScan()
{
    stationListSetScanStatus("scanning");

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function()
    {
        if (this.readyState == 4)
        {
            if (xhttp.status == 200)
            {                
                stationListSetScanStatus("idle");
                stationListRefresh(this.responseXML);
            }
            else
            {
                stationListSetScanStatus("failed");
                setTimeout(() =>
                {
                    stationListSetScanStatus("idle");
                }, 2000);
            }
        }
    };
    xhttp.open("GET", "scan.xml", true);
    xhttp.send();
}

function webRadioGetStations()
{
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function()
    {
        if (this.readyState == 4 && this.status == 200)
        {
            stationListRefresh(this.responseXML);
        }
    };
    xhttp.open("GET", "stations.xml", true);
    xhttp.send();
}

webRadioGetStations();
