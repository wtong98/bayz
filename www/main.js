/**
 * Logic for controlling browser-side audio production with webaudio
 * 
 * @author William Tong
 */

let audioCtx;

let servOn = false;
const pollDelay = 1000;
const bayzServer = 'http://localhost:42700';

const nameToKernel = {
    sine: sineKernel,
    fallback: sineKernel
}

const startButton = document.getElementById('start');
startButton.addEventListener('click', function(event){
    if (audioCtx == undefined) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)
    }

    if (servOn) {
        servOn = false;
        audioCtx.suspend()

        startButton.style.backgroundColor = "white";
        startButton.style.color = "black";
    } else {
        servOn = true;
        audioCtx.resume()

        startButton.style.backgroundColor = "#6d1aa1";
        startButton.style.color = "white";

        // let [osc, gain] = sineKernel();
        // intr = makeInstrument(osc, gain);
        // intr.start();
        // intr.play(60);

        poll(bayzServer);
    }
})

function poll(srvAddress) {
    axios.get(srvAddress).then((resp) => console.log(resp))
    if (servOn) {
        setTimeout(poll, pollDelay, srvAddress)
    }
}


function makeInstrument(osc, gain, attack=0.01, sustain=0.1, decay=0.03) {
    return {
        osc: osc,
        gain: gain,

        start() {
            gain.gain.value = 0;
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
        },

        stop() {
            gain.gain.setTargetAtTime(0, audioCtx.currentTime, decay);
        },

        cleanup() {
            osc.stop();
        },

        play(note, startTime=audioCtx.currentTime, stopTime=audioCtx.currentTime + 1) {
            osc.frequency.value = midiToFreq(note);
            gain.gain.setTargetAtTime(sustain, startTime, attack);
            gain.gain.setTargetAtTime(0, stopTime, decay);
        }

    }
}

function sineKernel() {
    osc = audioCtx.createOscillator();
    gainNode = audioCtx.createGain();
    osc.connect(gainNode);

    return [osc, gainNode];
}

function midiToFreq(m) {
    return Math.pow(2, (m - 69) / 12) * 440;
}