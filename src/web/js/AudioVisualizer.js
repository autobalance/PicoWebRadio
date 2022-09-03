/*
    Various helper functions to draw on the canvas.
*/
var canvas = document.getElementById("audio-visualizer");
var canvasContext = canvas.getContext("2d");

// Actual canvas width and height don't match the CSS (I think?), still figuring this out...
// Using the offset dimensions works for now
canvas.width = canvas.offsetWidth;
canvas.height = canvas.offsetHeight;

function canvasDrawBlack()
{
    canvasContext.fillStyle = "black";
    canvasContext.fillRect(0, 0, canvas.width, canvas.height);
}

// Draw a pause button in the middle of the canvas.
function canvasDrawPauseButton()
{
    canvasContext.fillStyle = "white";
    canvasContext.fillRect(canvas.width/2-5, canvas.height/2-10, 5, 20);
    canvasContext.fillRect(canvas.width/2+5, canvas.height/2-10, 5, 20);
}

// Display a 'Live' indicator in the top right corner of the canvas.
function canvasDrawLiveIndicator()
{
    canvasContext.fillStyle = "white";
    canvasContext.font = '16px Consolas';
    canvasContext.fillText("Live", canvas.width-50, 20);
    canvasContext.fillStyle = "red";
    canvasContext.fillRect(canvas.width-60, 10, 10, 10);
}








/*
    Functions to control actual audio playback.

    TODO: Playback of WAV files not supported on iOS/Safari (!), so figure out
          a way of loading WAV files using JavaScript and converting to e.g. MP3 on-the-fly.
          Real-time compression on the Pico may be possible using the second core,
          so look into that too.
*/

// TODO: Figure out how to extract sample rate after audio.load(),
//       either through reading WAV header or otherwise.
var audio = document.getElementById("audio");
var audioSampleRate = 30000;
var audioPlaying = false;

function startAudio()
{
    audio.src = window.location.protocol + '//' + window.location.hostname + ':1234/audio.wav';
    audio.preload = "none"; // setting preload to "none" doesn't seem to work on Chrome?
    audio.load();
    audio.play();
}
function stopAudio()
{
    audio.src = audio.src; // allows the stream to end when not playing (save bandwidth)
    audio.pause();
}





/*
    Functions to control the audio visualizer.

    Much help from the following sources:
        https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Visualizations_with_Web_Audio_API
        https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/getByteFrequencyData

    TODO: Implement setting to allow either scope view or current spectrum view (or disabled).
*/

var renderRequestID;

var audioContext = null;
var audioSource = null;
var audioAnalyser = null;

function startVisualizer()
{
    // initialize the audio context on user action (disabled AutoPlay cancels otherwise)
    if (audioContext == null)
    {
        audioContext = new AudioContext({sampleRate: audioSampleRate});
        audioAnalyser = audioContext.createAnalyser();

        audioSource = audioContext.createMediaElementSource(audio);
        audioSource.connect(audioAnalyser);

        // no distortion, connect directly to audio context
        audioAnalyser.connect(audioContext.destination);
    }

    audioAnalyser.fftSize = 128;
    const bufferLength = audioAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const lastDataArray = new Uint8Array(bufferLength);

    canvasDrawBlack();

    function drawSpectrum()
    {
        renderRequestID = requestAnimationFrame(drawSpectrum);

        audioAnalyser.getByteFrequencyData(dataArray);

        canvasDrawBlack();
        canvasDrawLiveIndicator();

        const gradFill = canvasContext.createLinearGradient(0, 0, 0, 640);
        gradFill.addColorStop(0, "green");
        gradFill.addColorStop(1, "blue");

        const barWidth = (canvas.width / bufferLength) * 0.6;
        const spaceWidth = (canvas.width / bufferLength) * 0.4;
        let barHeight;
        let x = 0;

        for (var i = 0; i < bufferLength; i++) {
            barHeight = dataArray[i];

            canvasContext.fillStyle = gradFill;
            canvasContext.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

            x += barWidth + spaceWidth;
        }
    }

    drawSpectrum();
};

function stopVisualizer()
{
    // set a timeout to have a smooth fade away of spectrum when audio stops
    setTimeout(() =>
    {
        cancelAnimationFrame(renderRequestID);
        canvasDrawBlack();
        canvasDrawPauseButton();
    }, 100);
};

canvas.addEventListener('click', function(event)
{
    if (audioPlaying)
    {
        stopAudio();
        stopVisualizer();
    }
    else
    {
        startAudio();
        startVisualizer();
    }
    audioPlaying = !audioPlaying;
}, false);

// Keep the canvas and spectrum resolution in line with window resizing.
// See: https://developer.mozilla.org/en-US/docs/Web/API/Window/resize_event
addEventListener('resize', (event) =>
{
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    if (audioPlaying)
    {
        cancelAnimationFrame(renderRequestID);
        startVisualizer();
    }
    else
    {
        canvasDrawBlack();
        canvasDrawPauseButton();
    }
});

// Draw initial black canvas with a pause button.
canvasDrawBlack();
canvasDrawPauseButton();
