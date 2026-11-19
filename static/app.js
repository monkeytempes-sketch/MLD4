const $ = (id) => document.getElementById(id);
const el = {
  file: $('file'), pick: $('pick'), cam: $('cam'), camclose: $('camclose'), go: $('go'),
  preview: $('preview'), video: $('video'), empty: $('empty'), stage: $('stage'),
  msg: $('msg'), err: $('err'), results: $('results'),
};
let blob = null;
let previewUrl = null;
let stream = null;

const setMessage = (t) => { el.msg.textContent = t; };
const clearError = () => { el.err.hidden = true; el.err.textContent = ''; };
const showError = (t) => { el.err.textContent = 'Galat: ' + t; el.err.hidden = false; };
const fmt = (v) => (v * 100).toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' %';

function stopCamera() {
  if (stream) stream.getTracks().forEach((t) => t.stop());
  stream = null;
  el.video.srcObject = null;
  el.video.hidden = true;
  el.camclose.hidden = true;
  el.cam.textContent = 'Buka kamera';
}

function setImage(b) {
  stopCamera();
  blob = b;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(b);
  el.preview.src = previewUrl;
  el.preview.hidden = false;
  el.empty.hidden = true;
  el.go.disabled = false;
  el.results.hidden = true;
  clearError();
  setMessage('Gambar siap. Tekan Identifikasi.');
}

function takeFile(file) {
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    showError('Berkas yang dipilih bukan gambar. Gunakan JPG atau PNG.');
    setMessage(blob ? 'Gambar sebelumnya tidak diganti.' : 'Pilih gambar untuk memulai.');
    return;
  }
  setImage(file);
}

async function onCamera() {
  if (stream) return capture();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError('Kamera tidak tersedia pada koneksi ini. Gunakan Pilih berkas.');
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
  } catch (e) {
    stream = null;
    showError('Kamera tidak dapat dibuka. Periksa izin kamera di browser.');
    return;
  }
  el.video.srcObject = stream;
  el.video.hidden = false;
  el.preview.hidden = true;
  el.empty.hidden = true;
  el.camclose.hidden = false;
  el.cam.textContent = 'Ambil foto';
  clearError();
  setMessage('Arahkan kamera ke satu baris tulisan, lalu tekan Ambil foto.');
}

function capture() {
  const v = el.video;
  if (!v.videoWidth) {
    showError('Kamera belum siap. Tunggu sebentar lalu coba lagi.');
    return;
  }
  const c = document.createElement('canvas');
  c.width = v.videoWidth;
  c.height = v.videoHeight;
  c.getContext('2d').drawImage(v, 0, 0);
  c.toBlob((b) => { if (b) setImage(b); }, 'image/jpeg', 0.95);
}

function renderList(listId, top) {
  const ol = $(listId);
  ol.replaceChildren();
  top.forEach((t, i) => {
    const li = document.createElement('li');
    const row = document.createElement('div');
    row.className = 'row';
    const kode = document.createElement('span');
    kode.className = 'kode';
    kode.textContent = t.kode;
    const nilai = document.createElement('span');
    nilai.className = 'nilai';
    nilai.textContent = fmt(t.nilai);
    row.append(kode, nilai);
    const bar = document.createElement('div');
    bar.className = 'bar';
    bar.setAttribute('aria-hidden', 'true');
    const fill = document.createElement('div');
    fill.className = 'fill' + (i === 0 ? ' first' : '');
    fill.style.width = Math.min(100, Math.max(0, t.nilai * 100)) + '%';
    bar.append(fill);
    li.append(row, bar);
    ol.append(li);
  });
}

function renderModel(prefix, data, glcmMs) {
  renderList(prefix + '-list', data.top);
  $(prefix + '-time').textContent = `Ekstraksi GLCM ${glcmMs.toFixed(0)} ms, prediksi ${data.waktu_ms.toFixed(0)} ms`;
  const best = data.top[0];
  const img = $(prefix + '-ex');
  img.src = best.contoh;
  img.alt = 'Contoh tulisan penulis ' + best.kode;
  $(prefix + '-cap').textContent = 'Contoh tulisan penulis ' + best.kode;
}

function render(data) {
  $('summary').textContent = data.ringkasan;
  const warn = $('warn');
  warn.replaceChildren();
  data.peringatan.forEach((w) => {
    const li = document.createElement('li');
    li.textContent = w;
    warn.append(li);
  });
  renderModel('svm', data.svm, data.waktu_glcm_ms);
  renderModel('rf', data.rf, data.waktu_glcm_ms);
  el.results.hidden = false;
  el.results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function identify() {
  if (!blob) return;
  clearError();
  el.go.disabled = true;
  el.go.textContent = 'Memproses';
  setMessage('Memproses gambar...');
  el.results.hidden = true;
  const fd = new FormData();
  fd.append('gambar', blob, 'gambar.jpg');
  try {
    const r = await fetch('/api/identifikasi', { method: 'POST', body: fd });
    let data = null;
    try { data = await r.json(); } catch (_) { data = null; }
    if (!r.ok || !data || !data.ok) {
      showError((data && data.pesan) || 'Server tidak merespons dengan benar.');
      setMessage('Identifikasi gagal.');
    } else {
      render(data);
      setMessage('Selesai.');
    }
  } catch (e) {
    showError('Tidak dapat menghubungi server. Pastikan aplikasi masih berjalan.');
    setMessage('Identifikasi gagal.');
  } finally {
    el.go.disabled = false;
    el.go.textContent = 'Identifikasi';
  }
}

el.pick.addEventListener('click', () => el.file.click());
el.file.addEventListener('change', () => { takeFile(el.file.files[0]); el.file.value = ''; });
el.cam.addEventListener('click', onCamera);
el.camclose.addEventListener('click', () => {
  stopCamera();
  if (blob) el.preview.hidden = false; else el.empty.hidden = false;
  setMessage(blob ? 'Gambar siap. Tekan Identifikasi.' : 'Pilih gambar untuk memulai.');
});
el.go.addEventListener('click', identify);

['dragenter', 'dragover'].forEach((ev) => el.stage.addEventListener(ev, (e) => { e.preventDefault(); el.stage.classList.add('drag'); }));
['dragleave', 'drop'].forEach((ev) => el.stage.addEventListener(ev, (e) => { e.preventDefault(); el.stage.classList.remove('drag'); }));
el.stage.addEventListener('drop', (e) => takeFile(e.dataTransfer.files[0]));

fetch('/api/info').then((r) => r.json()).then((i) => {
  const pct = (v) => (v * 100).toLocaleString('id-ID', { maximumFractionDigits: 1 });
  $('info').textContent = `Dilatih dengan ${i.jumlah_gambar} gambar dari ${i.jumlah_penulis} penulis. ` +
    `Akurasi uji rata-rata ${i.eksperimen} eksperimen: SVM ${pct(i.akurasi_svm)} %, Random Forest ${pct(i.akurasi_rf)} %.`;
}).catch(() => { $('info').textContent = 'Informasi model tidak tersedia.'; });
