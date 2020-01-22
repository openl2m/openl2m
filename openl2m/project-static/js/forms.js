$(document).ready(function() {
  // Flatpickr settings
  $("#dateTime").flatpickr({
    allowInput: true,
    enableSeconds: false,
    enableTime: true,
    time_24hr: true,
    minuteIncrement: 5,   // the default
    dateFormat: "Y-m-d H:i",
    minDate: "today",
    maxDate: new Date().fp_incr(28),    // 28 days from now
  });
});
