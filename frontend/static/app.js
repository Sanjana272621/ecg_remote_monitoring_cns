//Vitals
async function fetchVitals() {

    try {
        const [
            ecgResponse,
            respResponse,
            spo2Response,
            tempResponse,
            nibpResponse
        ] = await Promise.all([
            fetch("/ecg_vitals"),
            fetch("/resp_vitals"),
            fetch("/spo2_vitals"),
            fetch("/temp_vitals"),
            fetch("/nibp_vitals")
        ]);

        const ecg = await ecgResponse.json();
        const resp = await respResponse.json();
        const spo2 = await spo2Response.json();
        const temp = await tempResponse.json();
        const nibp = await nibpResponse.json();

        if (ecg.hrv !== undefined)
            document.getElementById("hrv").innerText = ecg.hrv;

        if (resp.resp_rate !== undefined)
            document.getElementById("resp_rate").innerText = resp.resp_rate;

        if (spo2.spo2_val !== undefined)
            document.getElementById("spo2_val").innerText = spo2.spo2_val;

        if (spo2.pr !== undefined)
            document.getElementById("pr").innerText = spo2.pr;

        if (temp.temp1 !== undefined)
            document.getElementById("temp1").innerText = temp.temp1;

        if (temp.temp2 !== undefined)
            document.getElementById("temp2").innerText = temp.temp2;

        if (nibp.sys !== undefined)
            document.getElementById("sys").innerText = nibp.sys;

        if (nibp.dia !== undefined)
            document.getElementById("dia").innerText = nibp.dia;

        if (nibp.map !== undefined)
            document.getElementById("map").innerText = nibp.map;

    } catch (err) {
        console.error("Vitals fetch failed:", err);
    }
}

setInterval(fetchVitals, 1000);
fetchVitals();

// WebSocket ECG waveform
document.addEventListener("DOMContentLoaded", () => {

    const protocol =
        window.location.protocol === "https:"
            ? "wss:"
            : "ws:";

    const socket =
        new WebSocket(
            `${protocol}//${window.location.host}/waveform`
        );

    const ecgILine = new TimeSeries();
    const ecgIILine = new TimeSeries();
    const ecgVLine = new TimeSeries();
    const respLine = new TimeSeries();
    const spo2Line = new TimeSeries();

    const chart = new SmoothieChart({
        millisPerPixel: 16,
        interpolation: "linear",

        minValue: -2000,
        maxValue: 2000,

        grid: {
            strokeStyle: "rgba(0,255,0,0.1)",
            fillStyle: "#000000",
            verticalSections: 4
        }
    });

    //helper to create all 5 charts
    function createChart(canvasId, line, opts = {}) {
        const chart = new SmoothieChart({
            millisPerPixel: opts.millisPerPixel ?? 18,
            interpolation: "linear",
            minValue: opts.minValue ?? -1000,
            maxValue: opts.maxValue ?? 1000,

            grid: {
                strokeStyle: "rgba(0,255,0,0.1)",
                fillStyle: "#000000",
                verticalSections: 4
            }
        });

        chart.addTimeSeries(line, {
            strokeStyle: "#00ff66",
            lineWidth: 1
        });

        chart.streamTo(
            document.getElementById(canvasId),
            0 //test with 0 delay
        );

        return chart;
    }

    // 5 charts
    createChart("ecgCanvasI", ecgILine);
    createChart("ecgCanvasII", ecgIILine);
    createChart("ecgCanvasV", ecgVLine);
    createChart("respCanvas", respLine, { millisPerPixel: 30, minValue: -500, maxValue: 500 });
    createChart("spo2Canvas", spo2Line, { millisPerPixel: 30, minValue: -500, maxValue: 500 });

    function appendWaveform(line, samples, key) {
        const n = samples.length;
        if (n === 0) return;

        const now = Date.now();
        const elapsed = now - lastBatchTime[key];
        const interval = elapsed / n;

        let t = lastBatchTime[key];
        samples.forEach(value => {
            const num = Number(value);
            if (!Number.isNaN(num)) {
                t += interval;
                line.append(t, num);
            }
        });

        lastBatchTime[key] = now;
    }

    let lastBatchTime = {
        ecgI: Date.now(),
        ecgII: Date.now(),
        ecgV: Date.now(),
        resp: Date.now(),
        spo2: Date.now()
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            appendWaveform(ecgILine, data.ecgI || [], "ecgI");
            appendWaveform(ecgIILine, data.ecgII || [], "ecgII");
            appendWaveform(ecgVLine, data.ecgV || [], "ecgV");
            appendWaveform(respLine, data.resp || [], "resp");
            appendWaveform(spo2Line, data.spo2 || [], "spo2");

        } catch (err) {
            console.error("[Waveform Parse Error]", err);
        }
    };
});

