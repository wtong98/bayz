/**
 * Logic for controlling browser-side audio production with webaudio
 * 
 * @author William Tong
 */

let audioCtx;

let servOn = false;
const pollDelay = 1000;
const tickDelay = 1000;
const bayzServer = 'http://localhost:42700';

const nameToKernel = {
    sine: sineKernel
}

const globalState = {
    current: undefined,
    proposed: undefined,
    ticker: Infinity,
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

        tick();
        poll(bayzServer);
    }
})

function tick() {
    globalState.ticker--;
    console.log('ticker', globalState.ticker);
    if (globalState.ticker == 0 || globalState.ticker == Infinity) {
        if (globalState.proposed != undefined) {
            globalState.current = globalState.proposed;
            globalState.proposed = undefined;
        }

        if (globalState.current != undefined) {
            globalState.ticker = globalState.current.cycleLength;
            globalState.current.blocks.map((b) => b.play(audioCtx.currentTime));
        }
    }

    if (servOn) {
        setTimeout(tick, tickDelay);
    }
}

function poll(srvAddress) {
    axios.get(srvAddress).then((resp) => consumeResp(resp.data));
    if (servOn) {
        setTimeout(poll, pollDelay, srvAddress);
    }
}

function consumeResp(respData) {
    console.log('recieve resp', respData);
    if (respData.deploy) {
        const cyc = respData.cycleLength;
        blocks = respData.sound.map((tag) => makeBlock(tag, cyc));
        proposeBlocks(blocks, cyc);
    }
}

function makeBlock(tag, cycleLength) {
    const opts = nameToKernel[tag.name]();
    const instrument = makeInstrument(...opts);
    instrument.start();

    return {
        instrument: instrument,

        play(cursor) {
            const duration = computeDuration(tag.notes, tag.rhythm);
            const unit = cycleLength / duration;

            tag.notes.map(function(note, i) {
                const len = tag.rhythm.length;
                const stopTime = cursor + tag.rhythm[i % len] * unit;

                instrument.play(note, cursor, stopTime);
                cursor = stopTime;
            });
        }
    }
}

function computeDuration(notes, rhythm) {
    const len = rhythm.length;
    total = notes.reduce(function(acc, _, i){
        return acc + rhythm[i % len];
    }, 0);

    return total;
}

function proposeBlocks(blocks, cycleLength) {
    const proposal = {
        blocks: blocks,
        cycleLength: cycleLength
    }

    globalState.proposed = proposal;
}



///////////////////////
///// INSTRUMENTS /////
///////////////////////

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
            setTimeout(()=>osc.stop(), 100);
        },

        play(note, startTime=audioCtx.currentTime, stopTime=audioCtx.currentTime + 1) {
            osc.frequency.setValueAtTime(midiToFreq(note), startTime, stopTime);
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