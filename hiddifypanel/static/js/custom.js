function ConvertNumberToPersion(elemnt) {
}

$(document).ready(function () {
  var isMouseOverMainSidebar = false;
  var isMouseOverSubSidebar = false;
  // Function to show the sub-sidebar
  function showSubSidebar(target) {
    $('.sub-sidebar').css({ 'display': 'block', 'opacity': 0, 'transform': 'translateX(-20px)' });
    $('#sub-sidebar > .nav-item').hide();
    $(target).show();
    setTimeout(function () {
      $('.sub-sidebar').css({ 'opacity': 1, 'transform': 'translateX(0)' });
    }, 200);
  }


  // Show the sub-sidebar when a main item is clicked or hovered
  $('#main-sidebar .nav-link').on('click mouseenter', function () {
    if ($(this).data('toggle') == 'modal' || ($(this).data('target') == undefined)) {
      hideSubSidebar()
      return;
    }
    // if ($(this).data('toggle')=='modal')return;
    showSubSidebar($(this).data('target'));
  });

  // Hide the sub-sidebar when clicking or hovering outside of it
  $(document).on('click', function (event) {
    if (!$(event.target).closest('.main-sidebar, .sub-sidebar').length) {
      hideSubSidebar();
    }
  });

  // Hide the sub-sidebar when the mouse leaves the sub-sidebar area
  $('.sub-sidebar').on('mouseenter', function () {
    isMouseOverSubSidebar = true;

  });

  $('.sub-sidebar').on('mouseleave', function () {
    isMouseOverSubSidebar = false;
    hideSubSidebar();
  });

  // Set a flag to prevent hiding the sub-sidebar when the mouse is over the main sidebar


  $('#main-sidebar [data-target]').on('mouseenter', function () {
    isMouseOverMainSidebar = true;
  });

  $('#main-sidebar [data-target]').on('mouseleave', function () {
    isMouseOverMainSidebar = false;
    //   hideSubSidebar();
  });

  // Modify the hideSubSidebar function to check the flag
  // Function to hide the sub-sidebar with animation
  function hideSubSidebar() {
    if (isMouseOverSubSidebar) return;
    if (isMouseOverMainSidebar) return;
    setTimeout(function () {
      if (!isMouseOverMainSidebar) {
        $('.sub-sidebar').css({ 'opacity': 0, 'transform': 'translateX(-20px)' });
        setTimeout(function () {
          $('.sub-sidebar').css('display', 'none');
        }, 200);
      }
    }, 10);

  }
});







