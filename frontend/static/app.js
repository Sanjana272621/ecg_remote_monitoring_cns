//Vitals
async function fetchVitals() {

    const response = await fetch("/vitals");

    const data = await response.json();

    // update all cards dynamically
    Object.keys(data).forEach(code => {

        const element = document.getElementById(code);

        if (element) {

            element.innerText =
                `${data[code].value} ${data[code].unit}`;
        }
    });
}

setInterval(fetchVitals, 2000);


//Websocket
document.addEventListener("DOMContentLoaded", () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(`${protocol}//${window.location.host}/waveform`);

    const line = new TimeSeries();
    const chart = new SmoothieChart({
        millisPerPixel: 16,
        interpolation: 'linear',
        minValue: -2000, //earlier -200
        maxValue: 2000, //earlier 900
        grid: {
            strokeStyle: 'rgba(0,255,0,0.1)',
            fillStyle: '#000000',
            verticalSections: 4
        }
    });

    const ecgCanvas = document.getElementById("ecgCanvas");
    ecgCanvas.width  = ecgCanvas.offsetWidth  || ecgCanvas.parentElement.clientWidth;
    ecgCanvas.height = ecgCanvas.offsetHeight || 148;

    chart.addTimeSeries(line, {
        strokeStyle: '#00ff66',
        lineWidth: 1,
        fillStyle: 'rgba(0, 0, 0, 0)'
    });

    chart.streamTo(ecgCanvas, 50);

    let baseClientTime = Date.now();
    let baseServerTime = 0;
    let sampleCount = 0;
    let nextTimestamp = Date.now();

    socket.onmessage = (event) => {
        try {
            const samples = JSON.parse(event.data);
            
            if (!Array.isArray(samples)) {
                console.warn('Expected array of samples, got:', typeof samples);
                return;
            }

            if (samples.length === 0) {
                return;
            }

            if (Array.isArray(samples[0])) {
                if (baseServerTime === 0) {
                    baseServerTime = samples[0][0];
                    console.log(`[ECG] Initialized: server_base=${baseServerTime}, client_base=${baseClientTime}`);
                }

                samples.forEach((sample) => {
                    if (Array.isArray(sample) && sample.length === 2) {
                        const [serverTime, value] = sample;
                        const num = Number(value);

                        if (!Number.isNaN(num)) {
                            const clientTime = baseClientTime + (serverTime - baseServerTime);
                            line.append(clientTime, num);
                            sampleCount++;
                        }
                    }
                });
            } else {
                //let sampleTime = Date.now();
                const sampleInterval = 24; // ms between raw samples for a smoother line shape
                                        // (2500 ecg samples / 1 minute)

                samples.forEach((value) => {
                    const num = Number(value);

                    if (!Number.isNaN(num)) {
                        line.append(nextTimestamp, num);
                        nextTimestamp += sampleInterval;
                        sampleCount++;
                    }
                });
            }
            
            if (sampleCount % 500 === 0) {
                console.log(`[ECG] Appended ${sampleCount} samples total`);
            }
        } catch (err) {
            console.error('[ECG Parse Error]', err);
        }
    };

    socket.onopen = () => console.log("[ECG] WebSocket connected to /waveform");
    socket.onclose = () => console.warn("[ECG] WebSocket closed");
    socket.onerror = (err) => console.error("[ECG] WebSocket error:", err);
});