$(document).ready(function() {
  /* Check if session has verifyDiv to show stored */
  if(typeof(Storage)!=="undefined" && sessionStorage.getItem('verifyToShow')) {
    var verifyToShow = sessionStorage.getItem('verifyToShow');
    $('.verifyDiv').addClass('hidden');
    $('.' + verifyToShow).removeClass('hidden');
  }
  $('.show-verifyDiv').click(function(event){
    event.preventDefault();
    var verifyToShow = $(this).data('verify');
     $('.verifyDiv').addClass('hidden');
     $('.verifyDiv').find('input').val('');
     $('.' + verifyToShow).removeClass('hidden');
     $('.' + verifyToShow).find('input').parsley().reset();
    if(typeof(Storage)!=="undefined") {
      sessionStorage.setItem('verifyToShow', verifyToShow);
    }
  });
});
