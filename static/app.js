const $ = (id) => document.getElementById(id);

const el = {
  file: $('file'),
  pick: $('pick'),
  cam: $('cam'),
  camclose: $('camclose'),
  go: $('go'),
  preview: $('preview'),
  video: $('video'),
  empty: $('empty'),
  stage: $('stage'),
  msg: $('msg'),
  err: $('err'),
  results: $('results'),
};

let blob = null;
let previewUrl = null;
let stream = null;

const MAX_UPLOAD_SIZE = 3.8 * 1024 * 1024;
const JPEG_QUALITY = 0.88;
const MAX_COMPRESS_ATTEMPTS = 5;

class UserError extends Error {}

const setMessage = (t) => {
  el.msg.textContent = t;
};

const clearError = () => {
  el.err.hidden = true;
  el.err.textContent = '';
};

const showError = (t) => {
  el.err.textContent = 'Galat: ' + t;
  el.err.hidden = false;
};

const fmt = (v) =>
  (v * 100).toLocaleString('id-ID', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }) + ' %';

async function compressForVercel(file) {
  if (file.size <= MAX_UPLOAD_SIZE) {
    return file;
  }

  setMessage('Mengoptimalkan ukuran gambar...');

  let bitmap;

  try {
    bitmap = await createImageBitmap(file);
  } catch (_) {
    throw new UserError(
      'Gambar tidak dapat dibaca. Gunakan JPG atau PNG.'
    );
  }

  try {
    let scale = Math.min(
      1,
      3000 / Math.max(bitmap.width, bitmap.height)
    );

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    for (let attempt = 0; attempt < MAX_COMPRESS_ATTEMPTS; attempt++) {
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));

      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);

      const compressed = await new Promise((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY);
      });

      if (!compressed) {
        break;
      }

      if (compressed.size <= MAX_UPLOAD_SIZE) {
        return new File([compressed], 'gambar.jpg', {
          type: 'image/jpeg',
          lastModified: Date.now(),
        });
      }

      scale *= Math.max(
        0.5,
        Math.sqrt(MAX_UPLOAD_SIZE / compressed.size) * 0.95
      );
    }

    throw new UserError(
      'Ukuran gambar masih terlalu besar setelah kompresi.'
    );
  } finally {
    bitmap.close();
  }
}

function cameraErrorMessage(e) {
  switch (e && e.name) {
    case 'NotAllowedError':
    case 'SecurityError':
      return 'Izin kamera ditolak. Aktifkan izin kamera di pengaturan browser.';
    case 'NotFoundError':
    case 'OverconstrainedError':
      return 'Kamera tidak ditemukan pada perangkat ini. Gunakan Pilih berkas.';
    case 'NotReadableError':
    case 'AbortError':
      return 'Kamera sedang dipakai aplikasi lain. Tutup aplikasi itu lalu coba lagi.';
    default:
      return 'Kamera tidak dapat dibuka. Gunakan Pilih berkas.';
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
  }

  stream = null;
  el.video.srcObject = null;
  el.video.hidden = true;
  el.camclose.hidden = true;
  el.cam.textContent = 'Buka kamera';
  el.go.disabled = !blob;
}

function setImage(b) {
  stopCamera();

  blob = b;

  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }

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
    showError(
      'Berkas yang dipilih bukan gambar. Gunakan JPG atau PNG.'
    );

    setMessage(
      blob
        ? 'Gambar sebelumnya tidak diganti.'
        : 'Pilih gambar untuk memulai.'
    );

    return;
  }

  setImage(file);
}

async function onCamera() {
  if (stream) {
    return capture();
  }

  if (
    !navigator.mediaDevices ||
    !navigator.mediaDevices.getUserMedia
  ) {
    showError(
      'Kamera tidak tersedia pada koneksi ini. Gunakan Pilih berkas.'
    );
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment',
      },
      audio: false,
    });
  } catch (e) {
    stream = null;
    console.error(e);
    showError(cameraErrorMessage(e));
    return;
  }

  el.video.srcObject = stream;
  el.video.hidden = false;
  el.preview.hidden = true;
  el.empty.hidden = true;
  el.camclose.hidden = false;
  el.cam.textContent = 'Ambil foto';
  el.go.disabled = true;

  clearError();

  setMessage(
    'Arahkan kamera ke satu baris tulisan, lalu tekan Ambil foto.'
  );
}

function capture() {
  const v = el.video;

  if (!v.videoWidth) {
    showError(
      'Kamera belum siap. Tunggu sebentar lalu coba lagi.'
    );
    return;
  }

  const c = document.createElement('canvas');

  c.width = v.videoWidth;
  c.height = v.videoHeight;

  c.getContext('2d').drawImage(v, 0, 0);

  c.toBlob(
    (b) => {
      if (b) {
        setImage(b);
      }
    },
    'image/jpeg',
    0.95
  );
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

    fill.className =
      'fill' + (i === 0 ? ' first' : '');

    fill.style.width =
      Math.min(100, Math.max(0, t.nilai * 100)) + '%';

    bar.append(fill);
    li.append(row, bar);
    ol.append(li);
  });
}

function renderModel(prefix, data, glcmMs) {
  renderList(prefix + '-list', data.top);

  $(prefix + '-time').textContent =
    `Ekstraksi GLCM ${glcmMs.toFixed(0)} ms, ` +
    `prediksi ${data.waktu_ms.toFixed(0)} ms`;

  const best = data.top[0];

  const img = $(prefix + '-ex');

  img.src = best.contoh;

  $(prefix + '-cap').textContent =
    'Contoh tulisan penulis ' + best.kode;

  return img;
}

async function render(data) {
  $('summary').textContent = data.ringkasan;

  const warn = $('warn');
  warn.replaceChildren();

  (data.peringatan || []).forEach((w) => {
    const li = document.createElement('li');
    li.textContent = w;
    warn.append(li);
  });

  const examples = [
    renderModel('svm', data.svm, data.waktu_glcm_ms),
    renderModel('rf', data.rf, data.waktu_glcm_ms),
  ];

  setMessage('Memuat contoh tulisan...');

  await Promise.all(examples.map((img) => img.decode().catch(() => {})));

  el.results.hidden = false;

  const heading = $('h-res');
  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });

  const reduceMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  el.results.scrollIntoView({
    behavior: reduceMotion ? 'auto' : 'smooth',
    block: 'start',
  });
}

async function identify() {
  if (!blob) return;

  clearError();

  el.go.disabled = true;
  el.go.textContent = 'Memproses';

  setMessage('Menyiapkan gambar...');
  el.results.hidden = true;

  try {
    const compressed = await compressForVercel(blob);

    const fd = new FormData();

    fd.append('gambar', compressed, compressed.name || 'gambar.jpg');

    setMessage('Mengirim dan memproses gambar...');

    let r;

    try {
      r = await fetch('/api/identifikasi', {
        method: 'POST',
        body: fd,
      });
    } catch (e) {
      console.error(e);
      throw new UserError(
        'Tidak dapat menghubungi server. Pastikan aplikasi masih berjalan.'
      );
    }

    let data = null;

    try {
      data = await r.json();
    } catch (_) {
      data = null;
    }

    if (!r.ok || !data || !data.ok) {
      showError(
        (data && data.pesan) ||
        'Server tidak merespons dengan benar.'
      );

      setMessage('Identifikasi gagal.');
    } else {
      await render(data);
      setMessage('Selesai.');
    }
  } catch (e) {
    console.error('Identifikasi gagal:', e);

    showError(
      e instanceof UserError
        ? e.message
        : 'Terjadi kesalahan tak terduga. Coba lagi.'
    );

    setMessage('Identifikasi gagal.');
  } finally {
    el.go.disabled = !blob || stream !== null;
    el.go.textContent = 'Identifikasi';
  }
}

el.pick.addEventListener('click', () => {
  el.file.click();
});

el.file.addEventListener('change', () => {
  takeFile(el.file.files[0]);
  el.file.value = '';
});

el.cam.addEventListener('click', onCamera);

el.camclose.addEventListener('click', () => {
  stopCamera();

  if (blob) {
    el.preview.hidden = false;
  } else {
    el.empty.hidden = false;
  }

  setMessage(
    blob
      ? 'Gambar siap. Tekan Identifikasi.'
      : 'Pilih gambar untuk memulai.'
  );
});

el.go.addEventListener('click', identify);

['dragenter', 'dragover'].forEach((ev) => {
  el.stage.addEventListener(ev, (e) => {
    e.preventDefault();
    el.stage.classList.add('drag');
  });
});

['dragleave', 'drop'].forEach((ev) => {
  el.stage.addEventListener(ev, (e) => {
    e.preventDefault();
    el.stage.classList.remove('drag');
  });
});

el.stage.addEventListener('drop', (e) => {
  takeFile(e.dataTransfer.files[0]);
});

fetch('/api/info')
  .then((r) => {
    if (!r.ok) {
      throw new Error('Gagal mengambil informasi model.');
    }

    return r.json();
  })
  .then((i) => {
    const pct = (v) =>
      (v * 100).toLocaleString('id-ID', {
        maximumFractionDigits: 1,
      });

    $('info').textContent =
      `Dilatih dengan ${i.jumlah_gambar} gambar dari ` +
      `${i.jumlah_penulis} penulis. ` +
      `Akurasi uji rata-rata ${i.eksperimen} eksperimen: ` +
      `SVM ${pct(i.akurasi_svm)} %, ` +
      `Random Forest ${pct(i.akurasi_rf)} %.`;
  })
  .catch((e) => {
    console.error(e);
    $('info').textContent =
      'Informasi model tidak tersedia.';
  });
