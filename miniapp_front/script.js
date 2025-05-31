document.getElementById('reviewForm')?.addEventListener('submit', function(e) {
  e.preventDefault(); this.reset(); document.getElementById('reviewMsg').style.display = 'block';
});
document.getElementById('searchForm')?.addEventListener('submit', function(e) {
  e.preventDefault(); this.reset(); document.getElementById('searchMsg').style.display = 'block';
});
