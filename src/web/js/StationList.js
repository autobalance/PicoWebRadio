/*
    Functions for altering the radio station sidebar.

    Much help from https://www.w3schools.com/howto/howto_js_sidenav.asp
*/
const stationSidebarElem = document.getElementById("station-list");
const stationSidebarHeader = document.getElementById("station-list-header");
const mainViewElem = document.getElementById("main");

var stationListVisible = true;
function stationListToggle()
{
    if (stationListVisible)
    {
        stationSidebarElem.style.width = "0";
        stationSidebarHeader.style.color = "#222";
        mainViewElem.style.marginLeft= "0";
    }
    else
    {
        stationSidebarElem.style.width = "250px";
        stationSidebarHeader.style.color = "#ccc";
        mainViewElem.style.marginLeft = "250px";
    }

    stationListVisible = !stationListVisible;
}

// Assuming first element of the list is the scan button.
// Maybe put the scan button as a separate item with its own CSS?
function stationListClear()
{
    const stationList = stationSidebarElem.getElementsByTagName('a');
    let stationListLen = stationList.length;
    for (var i = 1; i < stationListLen; i++)
    {
        stationList[1].remove();
    }
}

function stationListRefresh(stationXML)
{
    stationListClear();

    let stations = stationXML.getElementsByTagName("station");

    for (var i = 0; i < stations.length; i++)
    {
        let stationName = stations[i].getElementsByTagName("name")[0].innerHTML;
        let stationUrl = stations[i].getElementsByTagName("url")[0].innerHTML;

        let newStation = `<a href="javascript:void(0)"
                             style=""
                             onclick="webRadioTune('${stationUrl}', this)">
                          ${stationName}</a>`;

        stationSidebarElem.insertAdjacentHTML("beforeend", newStation);
    }
}

// Highlight the selected station in the list based on choice of 'status'
var lastStation;
function stationListUpdateSelection(station, status)
{
    if (lastStation)
    {
        lastStation.setAttribute('style', '');
    }

    if (status)
    {
        station.setAttribute('style', 'background-color: green; border-radius: 10px');
    }
    else
    {
        station.setAttribute('style', '');
    }

    lastStation = station;
}

function stationListSetScanStatus(scanStatus)
{
    const scanButton = stationSidebarElem.getElementsByTagName('a')[0];

    if (scanStatus === "idle")
    {
        scanButton.setAttribute('style', "background-color: gray; border-radius: 10px;");
        scanButton.innerText = 'Scan';
    }
    else if (scanStatus === "scanning")
    {
        scanButton.setAttribute('style', "background-color: green; border-radius: 10px;");
        scanButton.innerText = 'Scanning...';
    }
    else if (scanStatus === "failed")
    {
        scanButton.setAttribute('style', "background-color: red; border-radius: 10px;");
        scanButton.innerText = 'Scan failed!';
    }
}
