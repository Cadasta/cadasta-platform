/*
Inline Manual Player, v2.34.1
http://inlinemanual.com/
*/

// User tracking

window.inlineManualTracking = {
  uid: "{{ user.id }}",
  username: "{{ user.username }}"
}

// Embed correct player for site

var myplayer;
switch("{{ request.get_host }}") 
{
  case "platform.cadasta": 
    myplayer = "be355bb9f5ef5aaad63a2965ce033b56";
    break;
  case "demo.cadasta": 
    myplayer = "b4b392a6f77d7d0d6e04cee62b835187";
    break;
  default:
    myplayer = "c384a8ce835342a913859b2a50d1f6a9";
}

!function(){var e=document.createElement("script"),t=document.getElementsByTagName("script")[0];e.async=1,e.src="https://inlinemanual.com/embed/player." + myplayer + ".js",e.charset="UTF-8",t.parentNode.insertBefore(e,t)}();
