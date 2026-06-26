/* OpenL2M project-wide JS utilities */

function ol2mCopyText(text) {
  // Clipboard API requires a secure context (HTTPS / localhost).
  // Fall back to execCommand for plain HTTP dev access over an IP.
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;opacity:0;pointer-events:none';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try { document.execCommand('copy'); } finally { document.body.removeChild(ta); }
  return Promise.resolve();
}

document.addEventListener('click', function (e) {
  // Copy command output to clipboard
  var copyBtn = e.target.closest('.ol2m-copy-btn');
  if (copyBtn) {
    var pre = copyBtn.closest('.card').querySelector('.ol2m-cmd-pre');
    ol2mCopyText(pre.textContent.trim()).then(function () {
      var icon = copyBtn.querySelector('i');
      var orig = icon.className;
      icon.className = 'fa-solid fa-check';
      setTimeout(function () { icon.className = orig; }, 1500);
    });
    return;
  }

  // Download command output as a text file
  var dlBtn = e.target.closest('.ol2m-download-btn');
  if (dlBtn) {
    var pre = dlBtn.closest('.card').querySelector('.ol2m-cmd-pre');
    var name = (dlBtn.getAttribute('data-command') || 'output')
                 .replace(/[^a-zA-Z0-9_\-]/g, '_').slice(0, 64);
    var blob = new Blob([pre.textContent.trim()], { type: 'text/plain' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name + '.txt';
    a.click();
    URL.revokeObjectURL(a.href);
  }
});
