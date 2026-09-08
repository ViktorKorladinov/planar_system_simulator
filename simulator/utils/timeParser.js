export function formatTimestamp(str) {
  if (!str) return 'Unknown Date';
  let d, m, h, min;
  
  if (typeof str === 'string' && str.includes('_')) {
    [d, m, h, min] = str.split('_').map(Number);
  } else {
    const date = new Date(str);
    if (isNaN(date.getTime())) return 'Unknown Date';
    d = date.getDate();
    m = date.getMonth() + 1;
    h = date.getHours();
    min = date.getMinutes();
  }

  const months = ['January','February','March','April','May','June',
    'July','August','September','October','November','December'];
  const ord = n => n + (['st','nd','rd'][((n%100>>3)^1&&n%10)-1] || 'th');
  return `${ord(d)} of ${months[m - 1]}, ${h}:${String(min).padStart(2, '0')}`;
}