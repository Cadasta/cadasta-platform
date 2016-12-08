# Change Log

## [v1.3.0-alpha.3](https://github.com/Cadasta/cadasta-platform/tree/v1.3.0-alpha.3) (2016-12-08)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.3.0-alpha.2...v1.3.0-alpha.3)

**Fixed bugs:**

- Broken password reset on staging  [\#984](https://github.com/Cadasta/cadasta-platform/issues/984)
- Data Collector User Can't Download Forms [\#978](https://github.com/Cadasta/cadasta-platform/issues/978)
- XForms missing constraints and default values [\#969](https://github.com/Cadasta/cadasta-platform/issues/969)
- Refine user messaging and flow for anonymous users [\#677](https://github.com/Cadasta/cadasta-platform/issues/677)

**Merged pull requests:**

- Fix \#984 -- Remove client-side validation [\#988](https://github.com/Cadasta/cadasta-platform/pull/988) ([oliverroick](https://github.com/oliverroick))
- Populate new question and group fields [\#987](https://github.com/Cadasta/cadasta-platform/pull/987) ([oliverroick](https://github.com/oliverroick))
- Fix error message text [\#986](https://github.com/Cadasta/cadasta-platform/pull/986) ([clash99](https://github.com/clash99))
- Fixed misspelling [\#981](https://github.com/Cadasta/cadasta-platform/pull/981) ([clash99](https://github.com/clash99))
- Loadpolicies bugfix & provisioning [\#980](https://github.com/Cadasta/cadasta-platform/pull/980) ([amplifi](https://github.com/amplifi))
- detach\_object\_resources now works for deferred objects [\#974](https://github.com/Cadasta/cadasta-platform/pull/974) ([linzjax](https://github.com/linzjax))
- Update changelog for staging release [\#968](https://github.com/Cadasta/cadasta-platform/pull/968) ([amplifi](https://github.com/amplifi))

## [v1.3.0-alpha.2](https://github.com/Cadasta/cadasta-platform/tree/v1.3.0-alpha.2) (2016-12-06)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.3.0-alpha.1...v1.3.0-alpha.2)

**Implemented enhancements:**

- Data import: support for xlsx format used in data download [\#832](https://github.com/Cadasta/cadasta-platform/issues/832)
- Party list and add party pages are unused [\#768](https://github.com/Cadasta/cadasta-platform/issues/768)
- Include AWS CLI for all envs [\#959](https://github.com/Cadasta/cadasta-platform/pull/959) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- Password reset is unavailable for users who have forgotten their password [\#950](https://github.com/Cadasta/cadasta-platform/issues/950)
- After PR \#944 was merged, projects have disappeared from the dashboard map [\#949](https://github.com/Cadasta/cadasta-platform/issues/949)
- As a superuser, activating a user fails [\#927](https://github.com/Cadasta/cadasta-platform/issues/927)
- User roles for projects and organizations are not assigned correctly. [\#914](https://github.com/Cadasta/cadasta-platform/issues/914)
- It's not possible to remove the URL for an organization or a project [\#537](https://github.com/Cadasta/cadasta-platform/issues/537)

**Closed issues:**

- Asynchronous loading of geographic features [\#931](https://github.com/Cadasta/cadasta-platform/issues/931)
- Switch to Argon2 hash algorithm [\#876](https://github.com/Cadasta/cadasta-platform/issues/876)
- Implement password validation criteria [\#735](https://github.com/Cadasta/cadasta-platform/issues/735)

**Merged pull requests:**

- PostGIS 2.3 for Travis builds [\#965](https://github.com/Cadasta/cadasta-platform/pull/965) ([oliverroick](https://github.com/oliverroick))
- Added party index to project subnav [\#963](https://github.com/Cadasta/cadasta-platform/pull/963) ([clash99](https://github.com/clash99))
- Password validation on registration page - client-side [\#962](https://github.com/Cadasta/cadasta-platform/pull/962) ([clash99](https://github.com/clash99))
- Password strength requirements implemented for server-side [\#958](https://github.com/Cadasta/cadasta-platform/pull/958) ([linzjax](https://github.com/linzjax))
- Fix \#950 -- Remove LoginRequiredMixin from PasswordResetView [\#952](https://github.com/Cadasta/cadasta-platform/pull/952) ([oliverroick](https://github.com/oliverroick))
- Fix \#949 -- Remove markerClusterGroup and initialize L.Deflate correctly [\#951](https://github.com/Cadasta/cadasta-platform/pull/951) ([oliverroick](https://github.com/oliverroick))
- Add asychronous loading to map views [\#948](https://github.com/Cadasta/cadasta-platform/pull/948) ([oliverroick](https://github.com/oliverroick))
- Fix handling of L.Deflate for location edit page [\#947](https://github.com/Cadasta/cadasta-platform/pull/947) ([oliverroick](https://github.com/oliverroick))
- User layout changes [\#942](https://github.com/Cadasta/cadasta-platform/pull/942) ([clash99](https://github.com/clash99))
- Questionnaire API [\#938](https://github.com/Cadasta/cadasta-platform/pull/938) ([oliverroick](https://github.com/oliverroick))
- Add suport for XLSX imports [\#898](https://github.com/Cadasta/cadasta-platform/pull/898) ([bjohare](https://github.com/bjohare))

## [v1.3.0-alpha.1](https://github.com/Cadasta/cadasta-platform/tree/v1.3.0-alpha.1) (2016-11-22)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.2.0...v1.3.0-alpha.1)

**Fixed bugs:**

- Org Admin should have Administrator role automatically assigned for all projects within organization [\#737](https://github.com/Cadasta/cadasta-platform/issues/737)

**Closed issues:**

- Improve performance of Leaflet.Deflate [\#932](https://github.com/Cadasta/cadasta-platform/issues/932)
- Edit Project Boundaries not working in Safari [\#929](https://github.com/Cadasta/cadasta-platform/issues/929)
- API cleanup [\#880](https://github.com/Cadasta/cadasta-platform/issues/880)
- API Documentation/Doc Box Set-up [\#667](https://github.com/Cadasta/cadasta-platform/issues/667)

**Merged pull requests:**

- Map interaction performance improvements [\#944](https://github.com/Cadasta/cadasta-platform/pull/944) ([oliverroick](https://github.com/oliverroick))
- Readme updates [\#941](https://github.com/Cadasta/cadasta-platform/pull/941) ([IknowJoseph](https://github.com/IknowJoseph))
- API Cleanup [\#940](https://github.com/Cadasta/cadasta-platform/pull/940) ([oliverroick](https://github.com/oliverroick))
- Disable functional tests for now [\#939](https://github.com/Cadasta/cadasta-platform/pull/939) ([ian-ross](https://github.com/ian-ross))
- Users can no longer edit org admins project permissions [\#934](https://github.com/Cadasta/cadasta-platform/pull/934) ([linzjax](https://github.com/linzjax))
- Update changelog for v1.2.0 [\#933](https://github.com/Cadasta/cadasta-platform/pull/933) ([amplifi](https://github.com/amplifi))

## [v1.2.0](https://github.com/Cadasta/cadasta-platform/tree/v1.2.0) (2016-11-11)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.2.0-alpha.5...v1.2.0)

**Implemented enhancements:**

- Inline manual conditional variables for sign in options \(project walkthrough\) [\#623](https://github.com/Cadasta/cadasta-platform/issues/623)
- Resources number on project overview [\#474](https://github.com/Cadasta/cadasta-platform/issues/474)

**Fixed bugs:**

- Users tab in top navigation disappears on certain pages [\#732](https://github.com/Cadasta/cadasta-platform/issues/732)
- Translations need to be updated [\#580](https://github.com/Cadasta/cadasta-platform/issues/580)

**Closed issues:**

- Functional tests fail intermittently on Travis [\#902](https://github.com/Cadasta/cadasta-platform/issues/902)
- Installation fails: pip 2 not installed because pip 1.5 already exists [\#900](https://github.com/Cadasta/cadasta-platform/issues/900)
- Resources should accept or convert audio files besides mp3 [\#683](https://github.com/Cadasta/cadasta-platform/issues/683)
- "Draw Rectangle" while defining project areas [\#464](https://github.com/Cadasta/cadasta-platform/issues/464)

**Merged pull requests:**

- Fix \#732: "Users" menu on password views [\#924](https://github.com/Cadasta/cadasta-platform/pull/924) ([ian-ross](https://github.com/ian-ross))

## [v1.2.0-alpha.5](https://github.com/Cadasta/cadasta-platform/tree/v1.2.0-alpha.5) (2016-11-10)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.2.0-alpha.4...v1.2.0-alpha.5)

**Fixed bugs:**

- Inline Manual player script still contains template variables [\#912](https://github.com/Cadasta/cadasta-platform/issues/912)
- Imported resource filenames should be randomized [\#911](https://github.com/Cadasta/cadasta-platform/issues/911)
- Error uploading questionnaires [\#907](https://github.com/Cadasta/cadasta-platform/issues/907)
- Creating a new relationship via the API throws exception.  [\#897](https://github.com/Cadasta/cadasta-platform/issues/897)
- API does not list relationships for a party [\#896](https://github.com/Cadasta/cadasta-platform/issues/896)
- Error unzipping download data file  [\#885](https://github.com/Cadasta/cadasta-platform/issues/885)
- original\_file field not set correctly on imported resources [\#884](https://github.com/Cadasta/cadasta-platform/issues/884)
- PATCH /api/v1/organizations/{organization\_slug}/projects/{project\_slug}/users/{username}/  [\#881](https://github.com/Cadasta/cadasta-platform/issues/881)
- Catch jsonattrs KeyError [\#715](https://github.com/Cadasta/cadasta-platform/issues/715)
- Resource photo orientation all landscape [\#552](https://github.com/Cadasta/cadasta-platform/issues/552)

**Merged pull requests:**

- Fix: \#884 and \#911 update original\_file field and randomize filenames for imported resources [\#921](https://github.com/Cadasta/cadasta-platform/pull/921) ([bjohare](https://github.com/bjohare))
- Re: \#902 -- Disable failing functional tests temporarily [\#920](https://github.com/Cadasta/cadasta-platform/pull/920) ([oliverroick](https://github.com/oliverroick))
- Add Indonesian translations [\#918](https://github.com/Cadasta/cadasta-platform/pull/918) ([ian-ross](https://github.com/ian-ross))
- Make image thumbnailing EXIF orientation-aware [\#917](https://github.com/Cadasta/cadasta-platform/pull/917) ([ian-ross](https://github.com/ian-ross))
- Moved user tracking to base [\#916](https://github.com/Cadasta/cadasta-platform/pull/916) ([clash99](https://github.com/clash99))
- Fix GDAL install [\#906](https://github.com/Cadasta/cadasta-platform/pull/906) ([oliverroick](https://github.com/oliverroick))
- Fix \#896 [\#905](https://github.com/Cadasta/cadasta-platform/pull/905) ([ian-ross](https://github.com/ian-ross))
- Fix \#881 -- Assign user instance when updating role via API [\#894](https://github.com/Cadasta/cadasta-platform/pull/894) ([oliverroick](https://github.com/oliverroick))

## [v1.2.0-alpha.4](https://github.com/Cadasta/cadasta-platform/tree/v1.2.0-alpha.4) (2016-11-07)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.2.0-alpha.3...v1.2.0-alpha.4)

**Implemented enhancements:**

- Project overview stats needs CSS adjustment for large numbers [\#872](https://github.com/Cadasta/cadasta-platform/issues/872)
- Support for WKT in Data Import  [\#831](https://github.com/Cadasta/cadasta-platform/issues/831)

**Fixed bugs:**

- Double "1." on Add Location Wizard page 1 [\#874](https://github.com/Cadasta/cadasta-platform/issues/874)
- PUT method for updating a project member produces Platform Error [\#873](https://github.com/Cadasta/cadasta-platform/issues/873)
- Project overview stats needs CSS adjustment for large numbers [\#872](https://github.com/Cadasta/cadasta-platform/issues/872)
- Drawing Tools Do Not Show Up in Safari [\#858](https://github.com/Cadasta/cadasta-platform/issues/858)
- Projects with large numbers of locations are unresponsive [\#801](https://github.com/Cadasta/cadasta-platform/issues/801)
- Duplicated locations when submitting via ODK  [\#792](https://github.com/Cadasta/cadasta-platform/issues/792)
- Inlinemanual help panel isn't working correctly [\#722](https://github.com/Cadasta/cadasta-platform/issues/722)
- Unhandled exception if user already exists [\#696](https://github.com/Cadasta/cadasta-platform/issues/696)
- xform errors are still visible after re-upload of working xform [\#679](https://github.com/Cadasta/cadasta-platform/issues/679)

**Closed issues:**

- Small screen member list isn't centered [\#859](https://github.com/Cadasta/cadasta-platform/issues/859)
- Missing API endpoints [\#822](https://github.com/Cadasta/cadasta-platform/issues/822)
- Design Data Import UI [\#565](https://github.com/Cadasta/cadasta-platform/issues/565)

**Merged pull requests:**

- Django upgrade to 1.9.11 [\#903](https://github.com/Cadasta/cadasta-platform/pull/903) ([oliverroick](https://github.com/oliverroick))
- CSS fixes [\#899](https://github.com/Cadasta/cadasta-platform/pull/899) ([clash99](https://github.com/clash99))
- Added script for removing file upload errors [\#895](https://github.com/Cadasta/cadasta-platform/pull/895) ([clash99](https://github.com/clash99))
- Updated help link, embedded player per site [\#892](https://github.com/Cadasta/cadasta-platform/pull/892) ([clash99](https://github.com/clash99))
- Adjusted stats number sizes and added parsley comment fix [\#891](https://github.com/Cadasta/cadasta-platform/pull/891) ([clash99](https://github.com/clash99))
- Removed extra number [\#890](https://github.com/Cadasta/cadasta-platform/pull/890) ([clash99](https://github.com/clash99))
- Fix \#858 -- Read map:init event details correctly [\#889](https://github.com/Cadasta/cadasta-platform/pull/889) ([oliverroick](https://github.com/oliverroick))
- Added missing record resource api endpoints, and FileStorageTestCase [\#888](https://github.com/Cadasta/cadasta-platform/pull/888) ([linzjax](https://github.com/linzjax))
- Upgrade to Django 1.9.10 [\#887](https://github.com/Cadasta/cadasta-platform/pull/887) ([oliverroick](https://github.com/oliverroick))
- Update Changelog [\#883](https://github.com/Cadasta/cadasta-platform/pull/883) ([amplifi](https://github.com/amplifi))
- Fix \#831: Add support for WKT in Data Import [\#882](https://github.com/Cadasta/cadasta-platform/pull/882) ([bjohare](https://github.com/bjohare))
- Duplicate xform submissions detected, additional resources attached [\#851](https://github.com/Cadasta/cadasta-platform/pull/851) ([linzjax](https://github.com/linzjax))

## [v1.2.0-alpha.3](https://github.com/Cadasta/cadasta-platform/tree/v1.2.0-alpha.3) (2016-10-28)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.2.0-alpha.2...v1.2.0-alpha.3)

**Implemented enhancements:**

- Make import data pages wizard-ized [\#793](https://github.com/Cadasta/cadasta-platform/issues/793)
- Increase length of choices tab labels in questionnaires from 200 chars to 2500 chars [\#775](https://github.com/Cadasta/cadasta-platform/issues/775)

**Fixed bugs:**

- Uploading a XLSForm with empty labels throws IntegrityError [\#869](https://github.com/Cadasta/cadasta-platform/issues/869)
- Internal server error 500 when trying to download data from a large project [\#857](https://github.com/Cadasta/cadasta-platform/issues/857)
- Geometry editing: cancel prevents further editing [\#781](https://github.com/Cadasta/cadasta-platform/issues/781)

**Closed issues:**

- Data import: limit csv file size [\#834](https://github.com/Cadasta/cadasta-platform/issues/834)
- Improve Performance django-jsonattrs [\#824](https://github.com/Cadasta/cadasta-platform/issues/824)

**Merged pull requests:**

- Add separate cache settings for jsonattrs [\#879](https://github.com/Cadasta/cadasta-platform/pull/879) ([amplifi](https://github.com/amplifi))
- Add useful \_\_repr\_\_ methods to models [\#878](https://github.com/Cadasta/cadasta-platform/pull/878) ([oliverroick](https://github.com/oliverroick))
- Fix \#857: Imported resources saved to wrong location [\#877](https://github.com/Cadasta/cadasta-platform/pull/877) ([bjohare](https://github.com/bjohare))
- Design for data import [\#871](https://github.com/Cadasta/cadasta-platform/pull/871) ([clash99](https://github.com/clash99))
- Fix None for translated labels [\#870](https://github.com/Cadasta/cadasta-platform/pull/870) ([ian-ross](https://github.com/ian-ross))

## [v1.2.0-alpha.2](https://github.com/Cadasta/cadasta-platform/tree/v1.2.0-alpha.2) (2016-10-26)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.2.0-alpha.1...v1.2.0-alpha.2)

**Fixed bugs:**

- Imported resources missing header row [\#860](https://github.com/Cadasta/cadasta-platform/issues/860)
- Import tool fails to import tenure\_relationship\_attributes [\#812](https://github.com/Cadasta/cadasta-platform/issues/812)

**Closed issues:**

- API / Platform Errors when adding projects and users using API or Platform [\#866](https://github.com/Cadasta/cadasta-platform/issues/866)

**Merged pull requests:**

- Fix \#866 -- Makeing sure organizaiton roles are always unique [\#868](https://github.com/Cadasta/cadasta-platform/pull/868) ([oliverroick](https://github.com/oliverroick))

## [v1.2.0-alpha.1](https://github.com/Cadasta/cadasta-platform/tree/v1.2.0-alpha.1) (2016-10-26)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.1.0...v1.2.0-alpha.1)

**Implemented enhancements:**

- Add support for select\_multiple attributes to data import [\#791](https://github.com/Cadasta/cadasta-platform/issues/791)
- Add an indicator to indicate which fields are required in all of our HTML forms [\#357](https://github.com/Cadasta/cadasta-platform/issues/357)
- Add client-side form validation where possible [\#322](https://github.com/Cadasta/cadasta-platform/issues/322)
- User list page should also display the user's full name [\#316](https://github.com/Cadasta/cadasta-platform/issues/316)
- uWSGI needs env vars [\#864](https://github.com/Cadasta/cadasta-platform/pull/864) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- Standard questionnaire making platform error for new projects [\#862](https://github.com/Cadasta/cadasta-platform/issues/862)
- Project resources view Attach button should not be visible to users who doesn't have permission to add resources [\#835](https://github.com/Cadasta/cadasta-platform/issues/835)
- Page and permissions caching [\#714](https://github.com/Cadasta/cadasta-platform/issues/714)
- Long xform errors break layout [\#678](https://github.com/Cadasta/cadasta-platform/issues/678)

**Closed issues:**

- Reset button ideally should not be present in the Edit Profile screen [\#844](https://github.com/Cadasta/cadasta-platform/issues/844)
- Error running manage.py loadpolicies [\#836](https://github.com/Cadasta/cadasta-platform/issues/836)
- Reverse full name and user name to be consistent with new pattern [\#818](https://github.com/Cadasta/cadasta-platform/issues/818)

**Merged pull requests:**

- Update changelog [\#867](https://github.com/Cadasta/cadasta-platform/pull/867) ([amplifi](https://github.com/amplifi))
- Add import support for select\_multiple attribute types and tenure relationship attributes [\#865](https://github.com/Cadasta/cadasta-platform/pull/865) ([bjohare](https://github.com/bjohare))
- Try to fix non-determinism in tests [\#856](https://github.com/Cadasta/cadasta-platform/pull/856) ([ian-ross](https://github.com/ian-ross))
- Parsley integration [\#852](https://github.com/Cadasta/cadasta-platform/pull/852) ([clash99](https://github.com/clash99))
- First round of performance improvements [\#850](https://github.com/Cadasta/cadasta-platform/pull/850) ([ian-ross](https://github.com/ian-ross))
- Display username first then full name on projects permissions page [\#841](https://github.com/Cadasta/cadasta-platform/pull/841) ([karenc](https://github.com/karenc))
- Allow accounts loadpolicies command to be run on its own [\#839](https://github.com/Cadasta/cadasta-platform/pull/839) ([karenc](https://github.com/karenc))
- Project resource view 'Attach' button hiding from users who doesn't have permission [\#838](https://github.com/Cadasta/cadasta-platform/pull/838) ([manoramahp](https://github.com/manoramahp))
- Display user's full name on user list page [\#837](https://github.com/Cadasta/cadasta-platform/pull/837) ([karenc](https://github.com/karenc))

## [v1.1.0](https://github.com/Cadasta/cadasta-platform/tree/v1.1.0) (2016-10-20)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.1.0-alpha.1...v1.1.0)

## [v1.1.0-alpha.1](https://github.com/Cadasta/cadasta-platform/tree/v1.1.0-alpha.1) (2016-10-20)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v1.0.0...v1.1.0-alpha.1)

**Closed issues:**

- Weed out duplicate database requests in templates [\#494](https://github.com/Cadasta/cadasta-platform/issues/494)

**Merged pull requests:**

- Fix 502 errors on resources list page [\#855](https://github.com/Cadasta/cadasta-platform/pull/855) ([seav](https://github.com/seav))
- Implement a changelog [\#854](https://github.com/Cadasta/cadasta-platform/pull/854) ([amplifi](https://github.com/amplifi))
- Resolve \#494: Reduce duplicate and unnecessary database requests [\#853](https://github.com/Cadasta/cadasta-platform/pull/853) ([seav](https://github.com/seav))

## [v1.0.0](https://github.com/Cadasta/cadasta-platform/tree/v1.0.0) (2016-10-19)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.3.0-alpha.5...v1.0.0)

**Implemented enhancements:**

- When user has no full name empty space there on top of that users' username in organization member side menu [\#758](https://github.com/Cadasta/cadasta-platform/issues/758)
- Submitting multiple parties or locations per xform submission [\#554](https://github.com/Cadasta/cadasta-platform/issues/554)
- Add Opbeat integration and configuration [\#849](https://github.com/Cadasta/cadasta-platform/pull/849) ([amplifi](https://github.com/amplifi))
- Provisioning for memcached support [\#845](https://github.com/Cadasta/cadasta-platform/pull/845) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- Deleted records are not detached from resources [\#803](https://github.com/Cadasta/cadasta-platform/issues/803)
- Adding a project cannot complete if there are many org members [\#796](https://github.com/Cadasta/cadasta-platform/issues/796)
- Superuser cannot view org member edit page [\#794](https://github.com/Cadasta/cadasta-platform/issues/794)
- Can't change a org members project permissions. [\#779](https://github.com/Cadasta/cadasta-platform/issues/779)
- CSS tweaks [\#771](https://github.com/Cadasta/cadasta-platform/issues/771)
- Clicking on resources tab gives 502 error sporadically [\#770](https://github.com/Cadasta/cadasta-platform/issues/770)
- Email verification for user accounts not recorded [\#766](https://github.com/Cadasta/cadasta-platform/issues/766)
- Canceling adding/editing a location does not work [\#719](https://github.com/Cadasta/cadasta-platform/issues/719)
- Send confirmation email when user changes their email address [\#676](https://github.com/Cadasta/cadasta-platform/issues/676)
- Geopoint parse failure when there are also geotrace and geoshape questions in xlsform [\#643](https://github.com/Cadasta/cadasta-platform/issues/643)
- Weird formatting of attribute labels when mulitlingual labels defined in xform [\#389](https://github.com/Cadasta/cadasta-platform/issues/389)

**Closed issues:**

- Previews for non-image resources [\#847](https://github.com/Cadasta/cadasta-platform/issues/847)
- Nothing happens on clicking the info symbol "i"  [\#842](https://github.com/Cadasta/cadasta-platform/issues/842)
- Inactive account page shown but no confirmation email received [\#821](https://github.com/Cadasta/cadasta-platform/issues/821)

**Merged pull requests:**

- Whitelisted all audio types except vnd.\* [\#848](https://github.com/Cadasta/cadasta-platform/pull/848) ([linzjax](https://github.com/linzjax))
- Fix \#719: Fix URL for canceling adding locations [\#819](https://github.com/Cadasta/cadasta-platform/pull/819) ([seav](https://github.com/seav))
- Fixes for multilingual XLS Forms [\#817](https://github.com/Cadasta/cadasta-platform/pull/817) ([ian-ross](https://github.com/ian-ross))
- Kavindya89 bugfix\#758 [\#809](https://github.com/Cadasta/cadasta-platform/pull/809) ([ian-ross](https://github.com/ian-ross))
- Fix for \#643 [\#808](https://github.com/Cadasta/cadasta-platform/pull/808) ([bjohare](https://github.com/bjohare))
- CSS adjustments [\#807](https://github.com/Cadasta/cadasta-platform/pull/807) ([clash99](https://github.com/clash99))
- Fix \#794: Avoid error when superuser views org member edit page [\#806](https://github.com/Cadasta/cadasta-platform/pull/806) ([seav](https://github.com/seav))
- added pre\_delete to detach resources from records [\#804](https://github.com/Cadasta/cadasta-platform/pull/804) ([linzjax](https://github.com/linzjax))
- Improvement to user accounts [\#798](https://github.com/Cadasta/cadasta-platform/pull/798) ([oliverroick](https://github.com/oliverroick))
- Caching for tutelary [\#747](https://github.com/Cadasta/cadasta-platform/pull/747) ([ian-ross](https://github.com/ian-ross))

## [v0.3.0-alpha.5](https://github.com/Cadasta/cadasta-platform/tree/v0.3.0-alpha.5) (2016-10-06)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.3.0-alpha.4...v0.3.0-alpha.5)

**Implemented enhancements:**

- select\_multiple in XLS forms is not currently supported [\#586](https://github.com/Cadasta/cadasta-platform/issues/586)

**Fixed bugs:**

- Icons for resources created by import not displayed [\#799](https://github.com/Cadasta/cadasta-platform/issues/799)
- Data import should skip blank, non-required attribute fields [\#788](https://github.com/Cadasta/cadasta-platform/issues/788)
- Server error when adding a new member in the org that has more than one page list of projecs [\#782](https://github.com/Cadasta/cadasta-platform/issues/782)
- Select multiple not compatible with data download [\#780](https://github.com/Cadasta/cadasta-platform/issues/780)
- Safari is auto-filling project name with contact name [\#773](https://github.com/Cadasta/cadasta-platform/issues/773)
- When adding new members to the organization, you can see archived projects [\#763](https://github.com/Cadasta/cadasta-platform/issues/763)
- Archived projects should not appear in project list [\#762](https://github.com/Cadasta/cadasta-platform/issues/762)
- Can't add a resource in a location uploading a file  [\#754](https://github.com/Cadasta/cadasta-platform/issues/754)
- XForms: Attribute groups with similar labels will override each other [\#748](https://github.com/Cadasta/cadasta-platform/issues/748)
- Can't add location resource when I'm an admin and created the project [\#743](https://github.com/Cadasta/cadasta-platform/issues/743)
- During resource upload, resources should be removed when user clicks the 'remove' link [\#582](https://github.com/Cadasta/cadasta-platform/issues/582)

**Closed issues:**

- Archived project detail page is still accessible [\#783](https://github.com/Cadasta/cadasta-platform/issues/783)
- Option to add new organization when creating new project [\#772](https://github.com/Cadasta/cadasta-platform/issues/772)

**Merged pull requests:**

- Move AWS deployment instructions [\#805](https://github.com/Cadasta/cadasta-platform/pull/805) ([ian-ross](https://github.com/ian-ross))
- Fix: \#799 [\#800](https://github.com/Cadasta/cadasta-platform/pull/800) ([bjohare](https://github.com/bjohare))
- Attempt "fix" for \#770 [\#797](https://github.com/Cadasta/cadasta-platform/pull/797) ([ian-ross](https://github.com/ian-ross))
- Ensure form submission is complete with fields in DataTables [\#795](https://github.com/Cadasta/cadasta-platform/pull/795) ([seav](https://github.com/seav))
- Fix \#788 Data import should skip blank, non-required attribute fields [\#790](https://github.com/Cadasta/cadasta-platform/pull/790) ([bjohare](https://github.com/bjohare))
- Only active projects appear on member permissions page [\#789](https://github.com/Cadasta/cadasta-platform/pull/789) ([linzjax](https://github.com/linzjax))
- Bugfix/\#582 [\#787](https://github.com/Cadasta/cadasta-platform/pull/787) ([oliverroick](https://github.com/oliverroick))
- Updated data download formatting for select\_multiple [\#784](https://github.com/Cadasta/cadasta-platform/pull/784) ([linzjax](https://github.com/linzjax))
- Fix missing ugettext call [\#767](https://github.com/Cadasta/cadasta-platform/pull/767) ([ian-ross](https://github.com/ian-ross))
- Archive filter appears even if pagination occurs [\#765](https://github.com/Cadasta/cadasta-platform/pull/765) ([linzjax](https://github.com/linzjax))
- Fix untranslatable strings mostly in templates [\#764](https://github.com/Cadasta/cadasta-platform/pull/764) ([ian-ross](https://github.com/ian-ross))
- Fixing https://github.com/Cadasta/cadasta-platform/issues/754 [\#757](https://github.com/Cadasta/cadasta-platform/pull/757) ([kavindya89](https://github.com/kavindya89))

## [v0.3.0-alpha.4](https://github.com/Cadasta/cadasta-platform/tree/v0.3.0-alpha.4) (2016-10-03)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.3.0-alpha.3...v0.3.0-alpha.4)

**Implemented enhancements:**

- Member permissions ui problem with save [\#627](https://github.com/Cadasta/cadasta-platform/issues/627)
- Reset password page needs some CSS love. [\#591](https://github.com/Cadasta/cadasta-platform/issues/591)
- Consider adding either site-wide or fine-grained search index robot settings [\#454](https://github.com/Cadasta/cadasta-platform/issues/454)
- Script to remove files from temporary directories on the app server [\#354](https://github.com/Cadasta/cadasta-platform/issues/354)
- Enhancement/\#354 Cron task to prune MEDIA\_ROOT files [\#752](https://github.com/Cadasta/cadasta-platform/pull/752) ([amplifi](https://github.com/amplifi))
- Enhancement/\#454 Search Index robots settings [\#751](https://github.com/Cadasta/cadasta-platform/pull/751) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- Cannot click on profile button while adding a project [\#593](https://github.com/Cadasta/cadasta-platform/issues/593)

**Closed issues:**

- Update "e-mail" to "email" in text on pages and email text [\#709](https://github.com/Cadasta/cadasta-platform/issues/709)
- Password Strength Enforcement [\#273](https://github.com/Cadasta/cadasta-platform/issues/273)

**Merged pull requests:**

- Enhancement \#566: Add support for CSV imports [\#760](https://github.com/Cadasta/cadasta-platform/pull/760) ([bjohare](https://github.com/bjohare))
- \#586: Added support for select\_multiple in xls forms [\#756](https://github.com/Cadasta/cadasta-platform/pull/756) ([linzjax](https://github.com/linzjax))
- Updated member permissions layout [\#755](https://github.com/Cadasta/cadasta-platform/pull/755) ([clash99](https://github.com/clash99))
- \#554: Questionnaires can include repeat groups of parties or locations. [\#738](https://github.com/Cadasta/cadasta-platform/pull/738) ([linzjax](https://github.com/linzjax))

## [v0.3.0-alpha.3](https://github.com/Cadasta/cadasta-platform/tree/v0.3.0-alpha.3) (2016-09-29)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.3.0-alpha.2...v0.3.0-alpha.3)

**Implemented enhancements:**

- Need for global project option [\#524](https://github.com/Cadasta/cadasta-platform/issues/524)
- Add Calendar Widget for Date Fields [\#461](https://github.com/Cadasta/cadasta-platform/issues/461)

**Fixed bugs:**

- Non-project members should not see "Congratulations" message [\#682](https://github.com/Cadasta/cadasta-platform/issues/682)
- Adding New Location - Drop Down Pulling from Name instead of Label [\#478](https://github.com/Cadasta/cadasta-platform/issues/478)

**Closed issues:**

- When adding a new relationship, "Relationship Type" should be shown instead of "Tenure Type" [\#740](https://github.com/Cadasta/cadasta-platform/issues/740)

**Merged pull requests:**

- Remove postgis-2.1 from .travis.yml [\#746](https://github.com/Cadasta/cadasta-platform/pull/746) ([oliverroick](https://github.com/oliverroick))
- Updating pages needing css, fixed long form name overflow, removed hy… [\#745](https://github.com/Cadasta/cadasta-platform/pull/745) ([clash99](https://github.com/clash99))
- Small fixes [\#741](https://github.com/Cadasta/cadasta-platform/pull/741) ([oliverroick](https://github.com/oliverroick))
- Questionnaire choice labels [\#739](https://github.com/Cadasta/cadasta-platform/pull/739) ([ian-ross](https://github.com/ian-ross))
- Resolve \#461: Add calendar picker for date attribute fields [\#734](https://github.com/Cadasta/cadasta-platform/pull/734) ([seav](https://github.com/seav))

## [v0.3.0-alpha.2](https://github.com/Cadasta/cadasta-platform/tree/v0.3.0-alpha.2) (2016-09-28)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.3.0-alpha.1...v0.3.0-alpha.2)

**Implemented enhancements:**

- Make pseudo-links behave more traditionally [\#615](https://github.com/Cadasta/cadasta-platform/issues/615)
- Clicking on a resource row doesn't automatically check the checkbox [\#595](https://github.com/Cadasta/cadasta-platform/issues/595)
- Editing location geometry is not intuitive [\#556](https://github.com/Cadasta/cadasta-platform/issues/556)

**Fixed bugs:**

- Drop down for org admin user should not be active on project permissions page [\#632](https://github.com/Cadasta/cadasta-platform/issues/632)
- Can't view members... but I can [\#609](https://github.com/Cadasta/cadasta-platform/issues/609)

**Merged pull requests:**

- Bugfix/\#682 [\#736](https://github.com/Cadasta/cadasta-platform/pull/736) ([manoramahp](https://github.com/manoramahp))
- Bugfix/\#615 [\#731](https://github.com/Cadasta/cadasta-platform/pull/731) ([oliverroick](https://github.com/oliverroick))
- Make SASS compilation work in dev VM again [\#730](https://github.com/Cadasta/cadasta-platform/pull/730) ([ian-ross](https://github.com/ian-ross))
- Fixing https://github.com/Cadasta/cadasta-platform/issues/632 [\#729](https://github.com/Cadasta/cadasta-platform/pull/729) ([oliverroick](https://github.com/oliverroick))
- Show member list only to an organization member : https://github.com/… [\#728](https://github.com/Cadasta/cadasta-platform/pull/728) ([manoramahp](https://github.com/manoramahp))
- fixing Clicking on a resource row doesn't automatically check the che… [\#725](https://github.com/Cadasta/cadasta-platform/pull/725) ([kavindya89](https://github.com/kavindya89))
- Resolve \#556: Improve geometry editing UI [\#720](https://github.com/Cadasta/cadasta-platform/pull/720) ([seav](https://github.com/seav))

## [v0.3.0-alpha.1](https://github.com/Cadasta/cadasta-platform/tree/v0.3.0-alpha.1) (2016-09-23)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.2.0...v0.3.0-alpha.1)

**Implemented enhancements:**

- Add DigitalGlobe Vivid Layer and options with OSM to Basemap Options [\#716](https://github.com/Cadasta/cadasta-platform/issues/716)
- Order permission roles according to level of permissions in select dropdown [\#650](https://github.com/Cadasta/cadasta-platform/issues/650)
- Default is not empty in dropdowns  [\#445](https://github.com/Cadasta/cadasta-platform/issues/445)
- Records Wireframes [\#168](https://github.com/Cadasta/cadasta-platform/issues/168)
- Extend worker process timeout from 20s to 60s [\#706](https://github.com/Cadasta/cadasta-platform/pull/706) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- User account dropdown does not work during the project add details page  [\#707](https://github.com/Cadasta/cadasta-platform/issues/707)
- Setting location\_geometry to geoshape causes weird formatting [\#698](https://github.com/Cadasta/cadasta-platform/issues/698)
- Removing a resource from the project does not affect resource count on dashboard. [\#674](https://github.com/Cadasta/cadasta-platform/issues/674)
- Review the platform code and templates for untranslatable texts [\#573](https://github.com/Cadasta/cadasta-platform/issues/573)
- Attach resources uploaded through xforms to appropriate entities [\#553](https://github.com/Cadasta/cadasta-platform/issues/553)

**Closed issues:**

- User messaging for anonymous users when browsing projects [\#711](https://github.com/Cadasta/cadasta-platform/issues/711)
- Can sign-in and use the platform without email-id verification. [\#695](https://github.com/Cadasta/cadasta-platform/issues/695)
- Change Highlighting on Sample forms so geotrace is white [\#691](https://github.com/Cadasta/cadasta-platform/issues/691)
- Add permission filtering the API [\#685](https://github.com/Cadasta/cadasta-platform/issues/685)
- Administrator cannot archive organization [\#550](https://github.com/Cadasta/cadasta-platform/issues/550)

**Merged pull requests:**

- Fix \#674: Fix resource count on project dashboard [\#721](https://github.com/Cadasta/cadasta-platform/pull/721) ([seav](https://github.com/seav))
- Resolve \#716: Add DigitalGlobe Vivid layer [\#717](https://github.com/Cadasta/cadasta-platform/pull/717) ([seav](https://github.com/seav))
- Resolve \#445: Add blank defaults for dropdowns [\#713](https://github.com/Cadasta/cadasta-platform/pull/713) ([seav](https://github.com/seav))
- Fixing Order permission roles according to level of permissions in se… [\#708](https://github.com/Cadasta/cadasta-platform/pull/708) ([ian-ross](https://github.com/ian-ross))
- Fixes formatting issue caused by setting location\_geometry to geoshape [\#699](https://github.com/Cadasta/cadasta-platform/pull/699) ([linzjax](https://github.com/linzjax))
- Allows multiple resources to be attached to objects uploaded through ODK [\#697](https://github.com/Cadasta/cadasta-platform/pull/697) ([linzjax](https://github.com/linzjax))
- Missing translations [\#689](https://github.com/Cadasta/cadasta-platform/pull/689) ([ian-ross](https://github.com/ian-ross))
- Archived organizations and projects are now frozen. [\#658](https://github.com/Cadasta/cadasta-platform/pull/658) ([linzjax](https://github.com/linzjax))

## [v0.2.0](https://github.com/Cadasta/cadasta-platform/tree/v0.2.0) (2016-09-15)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.2.0-alpha.2...v0.2.0)

**Implemented enhancements:**

- "Contact us" should have emailto link [\#631](https://github.com/Cadasta/cadasta-platform/issues/631)

**Fixed bugs:**

- GPX file type not accepted as resource [\#672](https://github.com/Cadasta/cadasta-platform/issues/672)
- Default tiff preview isn't showing [\#668](https://github.com/Cadasta/cadasta-platform/issues/668)
- Use username in place of empty full name [\#626](https://github.com/Cadasta/cadasta-platform/issues/626)

**Closed issues:**

- API Features for QGIS Plugin [\#653](https://github.com/Cadasta/cadasta-platform/issues/653)
- Add New Project Location - Project Extent  [\#598](https://github.com/Cadasta/cadasta-platform/issues/598)

**Merged pull requests:**

- Add permissions filtering [\#694](https://github.com/Cadasta/cadasta-platform/pull/694) ([oliverroick](https://github.com/oliverroick))
- Filter "Project extent" from location types [\#693](https://github.com/Cadasta/cadasta-platform/pull/693) ([ian-ross](https://github.com/ian-ross))
- Tiff default icon used for preview image [\#688](https://github.com/Cadasta/cadasta-platform/pull/688) ([clash99](https://github.com/clash99))
- Fix for show username in member permissions page [\#687](https://github.com/Cadasta/cadasta-platform/pull/687) ([kavindya89](https://github.com/kavindya89))
- \[v2\] Insert link to email into "contact us" phrases [\#684](https://github.com/Cadasta/cadasta-platform/pull/684) ([nathalier](https://github.com/nathalier))

## [v0.2.0-alpha.2](https://github.com/Cadasta/cadasta-platform/tree/v0.2.0-alpha.2) (2016-09-13)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.2.0-alpha.1...v0.2.0-alpha.2)

**Implemented enhancements:**

- Increase length of notes field from 500 characters to 2500 characters [\#659](https://github.com/Cadasta/cadasta-platform/issues/659)
- Ajax session to API authentication bridging [\#635](https://github.com/Cadasta/cadasta-platform/issues/635)
- Replace "i" link in header [\#622](https://github.com/Cadasta/cadasta-platform/issues/622)
- GPX Import [\#613](https://github.com/Cadasta/cadasta-platform/issues/613)
- Display user's friendly file name for resources [\#533](https://github.com/Cadasta/cadasta-platform/issues/533)
- API Polish and Release [\#447](https://github.com/Cadasta/cadasta-platform/issues/447)
- Provide Sample XLSForm to Users [\#403](https://github.com/Cadasta/cadasta-platform/issues/403)

**Fixed bugs:**

- MP3 file type not accepted as resource [\#671](https://github.com/Cadasta/cadasta-platform/issues/671)
- XML file type not accepted as resource [\#670](https://github.com/Cadasta/cadasta-platform/issues/670)
- DOCX file type not accepted as resource [\#669](https://github.com/Cadasta/cadasta-platform/issues/669)
- API: Anonymous users can view full project list [\#642](https://github.com/Cadasta/cadasta-platform/issues/642)
- Hamburger menu responsiveness [\#628](https://github.com/Cadasta/cadasta-platform/issues/628)
- Catch schema / attribute errors during project page load [\#614](https://github.com/Cadasta/cadasta-platform/issues/614)
- Footer glitching on smaller screen sizes on Organization Dashboards [\#606](https://github.com/Cadasta/cadasta-platform/issues/606)
- XLSForms with blank line in settings tab raise 500 Error [\#605](https://github.com/Cadasta/cadasta-platform/issues/605)
- Benghali font replacement [\#585](https://github.com/Cadasta/cadasta-platform/issues/585)

**Closed issues:**

- geo\_types not working fine with ODK in \*some\* Android devices [\#641](https://github.com/Cadasta/cadasta-platform/issues/641)
- Rationalise view testing approaches [\#488](https://github.com/Cadasta/cadasta-platform/issues/488)

**Merged pull requests:**

- Fix \#642: anonymous users can view full project list [\#681](https://github.com/Cadasta/cadasta-platform/pull/681) ([ian-ross](https://github.com/ian-ross))
- Fixes \#669, \#670 and \#671 [\#680](https://github.com/Cadasta/cadasta-platform/pull/680) ([bjohare](https://github.com/bjohare))
- Refactor view tests; use django-skivvy [\#673](https://github.com/Cadasta/cadasta-platform/pull/673) ([oliverroick](https://github.com/oliverroick))
- API cleanup [\#666](https://github.com/Cadasta/cadasta-platform/pull/666) ([oliverroick](https://github.com/oliverroick))
- Add Portuguese translations [\#665](https://github.com/Cadasta/cadasta-platform/pull/665) ([ian-ross](https://github.com/ian-ross))
- Updated questionnaire model to allow for 2500 character labels [\#661](https://github.com/Cadasta/cadasta-platform/pull/661) ([linzjax](https://github.com/linzjax))
- Org overview page and footer changes [\#657](https://github.com/Cadasta/cadasta-platform/pull/657) ([clash99](https://github.com/clash99))
- GPX Import \#613 [\#656](https://github.com/Cadasta/cadasta-platform/pull/656) ([bjohare](https://github.com/bjohare))
- Fixes \#533 -- Display user friendly file names [\#655](https://github.com/Cadasta/cadasta-platform/pull/655) ([oliverroick](https://github.com/oliverroick))

## [v0.2.0-alpha.1](https://github.com/Cadasta/cadasta-platform/tree/v0.2.0-alpha.1) (2016-09-08)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.1.1...v0.2.0-alpha.1)

**Implemented enhancements:**

- Don't show the party picker when adding a new relationship if there are no parties yet [\#612](https://github.com/Cadasta/cadasta-platform/issues/612)
- Create "Splash Screen" on dashboard [\#492](https://github.com/Cadasta/cadasta-platform/issues/492)
- Errors in Parsing XLSForm Should Happen Sooner than the Project Overview Page [\#272](https://github.com/Cadasta/cadasta-platform/issues/272)
- Missing "remove connection" from resource [\#261](https://github.com/Cadasta/cadasta-platform/issues/261)
- Add email notifications for unhandled exceptions and xform submission errors [\#630](https://github.com/Cadasta/cadasta-platform/pull/630) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- demo user credentials not working on staging/platform [\#624](https://github.com/Cadasta/cadasta-platform/issues/624)
- API: Members added to an organization are automatically assigned as administrators [\#608](https://github.com/Cadasta/cadasta-platform/issues/608)
- API: Deleting user from an organization member list completely deletes the user account [\#603](https://github.com/Cadasta/cadasta-platform/issues/603)
- Possible to select "All Types" for relationship type [\#588](https://github.com/Cadasta/cadasta-platform/issues/588)
- going to "my location" doesn't seem to work [\#551](https://github.com/Cadasta/cadasta-platform/issues/551)
- Organization Admin can delete herself, creating admin-less organization [\#548](https://github.com/Cadasta/cadasta-platform/issues/548)

**Closed issues:**

- Hide arabic option in language dropdown in footer [\#563](https://github.com/Cadasta/cadasta-platform/issues/563)
- Columns of Resources tables for each type of entity is not consistent [\#497](https://github.com/Cadasta/cadasta-platform/issues/497)

**Merged pull requests:**

- Fixing \#272 [\#652](https://github.com/Cadasta/cadasta-platform/pull/652) ([bjohare](https://github.com/bjohare))
- Safari fix for header menu in small screens [\#651](https://github.com/Cadasta/cadasta-platform/pull/651) ([clash99](https://github.com/clash99))
- Changes for adding new project details questionnaire [\#649](https://github.com/Cadasta/cadasta-platform/pull/649) ([clash99](https://github.com/clash99))
- Fixing \#643 [\#648](https://github.com/Cadasta/cadasta-platform/pull/648) ([bjohare](https://github.com/bjohare))
- Language support [\#647](https://github.com/Cadasta/cadasta-platform/pull/647) ([ian-ross](https://github.com/ian-ross))
- Resolve \#612: Don’t show party picker if there are no parties [\#646](https://github.com/Cadasta/cadasta-platform/pull/646) ([seav](https://github.com/seav))
- Resolve \#261 and \#497: Improve handling of resources [\#644](https://github.com/Cadasta/cadasta-platform/pull/644) ([seav](https://github.com/seav))
- Noto Sans Bengali font for Bengali replacement [\#639](https://github.com/Cadasta/cadasta-platform/pull/639) ([clash99](https://github.com/clash99))
- Force DRF Docs to provide Headers input [\#638](https://github.com/Cadasta/cadasta-platform/pull/638) ([ian-ross](https://github.com/ian-ross))
- Quick fix! [\#637](https://github.com/Cadasta/cadasta-platform/pull/637) ([ian-ross](https://github.com/ian-ross))
- Hiding arabic language option [\#636](https://github.com/Cadasta/cadasta-platform/pull/636) ([clash99](https://github.com/clash99))
- InlineManual changes [\#634](https://github.com/Cadasta/cadasta-platform/pull/634) ([clash99](https://github.com/clash99))
- Fix \#590: spatial unit visibility [\#633](https://github.com/Cadasta/cadasta-platform/pull/633) ([ian-ross](https://github.com/ian-ross))
- Admin users can no longer delete/demote themselves [\#625](https://github.com/Cadasta/cadasta-platform/pull/625) ([linzjax](https://github.com/linzjax))
- Fix organization users API issues [\#621](https://github.com/Cadasta/cadasta-platform/pull/621) ([ian-ross](https://github.com/ian-ross))
- Fix \#588: filter "All Types" from tenure type list [\#620](https://github.com/Cadasta/cadasta-platform/pull/620) ([ian-ross](https://github.com/ian-ross))

## [v0.1.1](https://github.com/Cadasta/cadasta-platform/tree/v0.1.1) (2016-08-30)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/stg...v0.1.1)

**Fixed bugs:**

- Error editing a location when field length is greater than 32 chars in a text field [\#557](https://github.com/Cadasta/cadasta-platform/issues/557)

**Merged pull requests:**

- Tidy up provisioning and loadstatic thing [\#619](https://github.com/Cadasta/cadasta-platform/pull/619) ([ian-ross](https://github.com/ian-ross))
- Removed loadstatic from provisioning. Attribute objects are no longer… [\#617](https://github.com/Cadasta/cadasta-platform/pull/617) ([linzjax](https://github.com/linzjax))
- Add custom 500 error page [\#616](https://github.com/Cadasta/cadasta-platform/pull/616) ([bjohare](https://github.com/bjohare))

## [stg](https://github.com/Cadasta/cadasta-platform/tree/stg) (2016-08-26)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/v0.1.0...stg)

**Implemented enhancements:**

- Edit Project Location should be changed to Edit Project Boundary [\#596](https://github.com/Cadasta/cadasta-platform/issues/596)
- Org overview blank text [\#510](https://github.com/Cadasta/cadasta-platform/issues/510)
- Long titles flow outside of page header [\#471](https://github.com/Cadasta/cadasta-platform/issues/471)
- Back Button When in process of adding new project [\#465](https://github.com/Cadasta/cadasta-platform/issues/465)
- Check button consistency across the platform [\#443](https://github.com/Cadasta/cadasta-platform/issues/443)
- Model for entire XForm submission? [\#442](https://github.com/Cadasta/cadasta-platform/issues/442)
- Improve party selection widget [\#441](https://github.com/Cadasta/cadasta-platform/issues/441)
- django-buckets: upload\_to option should auto-generate folders [\#434](https://github.com/Cadasta/cadasta-platform/issues/434)
- Forms Download to ODK should have human names [\#412](https://github.com/Cadasta/cadasta-platform/issues/412)
- Combine add resource options [\#407](https://github.com/Cadasta/cadasta-platform/issues/407)
- Improve map pop-over button [\#406](https://github.com/Cadasta/cadasta-platform/issues/406)
- Update map geometry field error [\#397](https://github.com/Cadasta/cadasta-platform/issues/397)
- Clean-up Loading of Static Data Set-up [\#383](https://github.com/Cadasta/cadasta-platform/issues/383)
- Add details to org and project overview [\#372](https://github.com/Cadasta/cadasta-platform/issues/372)
- Remove "spatial units" text in error message [\#371](https://github.com/Cadasta/cadasta-platform/issues/371)
- Change message to not be all caps [\#368](https://github.com/Cadasta/cadasta-platform/issues/368)
- File icons for resource list thumbnail previews [\#355](https://github.com/Cadasta/cadasta-platform/issues/355)
- Location error messaging [\#345](https://github.com/Cadasta/cadasta-platform/issues/345)
- CSS outstanding pages [\#344](https://github.com/Cadasta/cadasta-platform/issues/344)
- Connect map click on project overview to map tab [\#325](https://github.com/Cadasta/cadasta-platform/issues/325)
- Prevent duplicate organization names and duplicate project names within the same organization [\#324](https://github.com/Cadasta/cadasta-platform/issues/324)
- Fine-tune response css [\#266](https://github.com/Cadasta/cadasta-platform/issues/266)
- Project overview page's ellipsis menu should adapt based on the user's permissions [\#183](https://github.com/Cadasta/cadasta-platform/issues/183)
- Integrate language translation option [\#78](https://github.com/Cadasta/cadasta-platform/issues/78)
- nginx config update to serve over SSL [\#522](https://github.com/Cadasta/cadasta-platform/pull/522) ([amplifi](https://github.com/amplifi))

**Fixed bugs:**

- Cannot cancel edit resource if changes are made [\#594](https://github.com/Cadasta/cadasta-platform/issues/594)
- No xform submission error logging output in debug.log [\#583](https://github.com/Cadasta/cadasta-platform/issues/583)
- Organization name with non-Latin characters in dashboard popover [\#578](https://github.com/Cadasta/cadasta-platform/issues/578)
- Error Checking for Geotypes colliding w/being able to select Geotypes in XLSForms [\#577](https://github.com/Cadasta/cadasta-platform/issues/577)
- Questionnaire data migration failing [\#570](https://github.com/Cadasta/cadasta-platform/issues/570)
- User name in header bug [\#543](https://github.com/Cadasta/cadasta-platform/issues/543)
- Project data is not preserved when stepping back in the add project wizard [\#530](https://github.com/Cadasta/cadasta-platform/issues/530)
- Project contacts aren't saved on project creation [\#528](https://github.com/Cadasta/cadasta-platform/issues/528)
- Deduplicated slug names are not formatted as expected [\#527](https://github.com/Cadasta/cadasta-platform/issues/527)
- Default form submit in step 2 or 3 of the add project wizard is the Previous button [\#525](https://github.com/Cadasta/cadasta-platform/issues/525)
- Ellipsis menu disappears when on page in ellipsis menu [\#520](https://github.com/Cadasta/cadasta-platform/issues/520)
- Adding resources not on page 1 of library broken [\#507](https://github.com/Cadasta/cadasta-platform/issues/507)
- Resources table is not responsive [\#498](https://github.com/Cadasta/cadasta-platform/issues/498)
- XLSForm parse errors fail silently [\#480](https://github.com/Cadasta/cadasta-platform/issues/480)
- Weird maintenance of state in the contacts form   [\#476](https://github.com/Cadasta/cadasta-platform/issues/476)
- Error in URL when adding new organization [\#463](https://github.com/Cadasta/cadasta-platform/issues/463)
- Projects, Organizations...and Users from homepage [\#462](https://github.com/Cadasta/cadasta-platform/issues/462)
- Users tab [\#452](https://github.com/Cadasta/cadasta-platform/issues/452)
- Odd highlighting around resource checkboxes [\#436](https://github.com/Cadasta/cadasta-platform/issues/436)
- Max Length of Project name input box is 100 should be 50 [\#414](https://github.com/Cadasta/cadasta-platform/issues/414)
- Resources tab visibility [\#409](https://github.com/Cadasta/cadasta-platform/issues/409)
- Contacts Error Message Not Consistent with other error messaging [\#364](https://github.com/Cadasta/cadasta-platform/issues/364)
- Website throws an errors when you delete the single contacts row and then submit [\#315](https://github.com/Cadasta/cadasta-platform/issues/315)
- Don't display the add project link/button if the user does not have the project.create permission [\#185](https://github.com/Cadasta/cadasta-platform/issues/185)
- When adding a new project, the list of selectable orgs should be limited [\#184](https://github.com/Cadasta/cadasta-platform/issues/184)

**Closed issues:**

- Question: Select Geotype in Your XLSForm [\#521](https://github.com/Cadasta/cadasta-platform/issues/521)
- Rationalise functional testing approaches [\#503](https://github.com/Cadasta/cadasta-platform/issues/503)
- Set up Django debug toolbar [\#489](https://github.com/Cadasta/cadasta-platform/issues/489)
- Investigate Travis setup caching [\#487](https://github.com/Cadasta/cadasta-platform/issues/487)
- Speed up Travis platform setup [\#486](https://github.com/Cadasta/cadasta-platform/issues/486)
- Rationalise permissions checking [\#485](https://github.com/Cadasta/cadasta-platform/issues/485)
- Adding Location - Character Limit on Notes [\#479](https://github.com/Cadasta/cadasta-platform/issues/479)
- Permission Denied when Adding New Project [\#468](https://github.com/Cadasta/cadasta-platform/issues/468)
- Server 500 Error when creating a new project.... [\#466](https://github.com/Cadasta/cadasta-platform/issues/466)
- Remove all randomised test cases from functional tests [\#457](https://github.com/Cadasta/cadasta-platform/issues/457)
- Prototype switchover to Leaflet 1.0.0-rc2 [\#450](https://github.com/Cadasta/cadasta-platform/issues/450)
- Extra scrollbars in dashboard map UI [\#449](https://github.com/Cadasta/cadasta-platform/issues/449)
- Rework default data table search/ pagination options [\#446](https://github.com/Cadasta/cadasta-platform/issues/446)
- XForms need a unique way to identify associated questionnaire. [\#440](https://github.com/Cadasta/cadasta-platform/issues/440)
- Location details - Empty resource starter text [\#427](https://github.com/Cadasta/cadasta-platform/issues/427)
- Should the project geometry/extent be required? [\#358](https://github.com/Cadasta/cadasta-platform/issues/358)
- Handle changes to attribute schema selector fields [\#350](https://github.com/Cadasta/cadasta-platform/issues/350)
- Shapefile Export [\#323](https://github.com/Cadasta/cadasta-platform/issues/323)
- Don't show the "Add from library" tab/button if there are no resources in the library [\#295](https://github.com/Cadasta/cadasta-platform/issues/295)
- Double modals [\#283](https://github.com/Cadasta/cadasta-platform/issues/283)
- Multiple scrollbars [\#249](https://github.com/Cadasta/cadasta-platform/issues/249)
- DRF docs does not work with versions [\#134](https://github.com/Cadasta/cadasta-platform/issues/134)
- History [\#28](https://github.com/Cadasta/cadasta-platform/issues/28)
- Monitoring and Reporting [\#16](https://github.com/Cadasta/cadasta-platform/issues/16)

**Merged pull requests:**

- Bump django-jsonattr version [\#607](https://github.com/Cadasta/cadasta-platform/pull/607) ([ian-ross](https://github.com/ian-ross))
- Added people tracking [\#604](https://github.com/Cadasta/cadasta-platform/pull/604) ([clash99](https://github.com/clash99))
- Fix \#594: Correct edit resource cancel button URL [\#602](https://github.com/Cadasta/cadasta-platform/pull/602) ([seav](https://github.com/seav))
- Update django-jsonattrs to version 0.1.8 [\#601](https://github.com/Cadasta/cadasta-platform/pull/601) ([ian-ross](https://github.com/ian-ross))
- Embedded player for demo site [\#600](https://github.com/Cadasta/cadasta-platform/pull/600) ([clash99](https://github.com/clash99))
- Resolve \#596: Use "boundary" instead of "location" [\#599](https://github.com/Cadasta/cadasta-platform/pull/599) ([seav](https://github.com/seav))
- Update template to force SSL for all platform and API URLs [\#589](https://github.com/Cadasta/cadasta-platform/pull/589) ([amplifi](https://github.com/amplifi))
- Improved logging configuration [\#584](https://github.com/Cadasta/cadasta-platform/pull/584) ([bjohare](https://github.com/bjohare))
- Resolve \#510: Improve messaging on orgs with no projects [\#574](https://github.com/Cadasta/cadasta-platform/pull/574) ([seav](https://github.com/seav))
- Fix for \#570 [\#571](https://github.com/Cadasta/cadasta-platform/pull/571) ([bjohare](https://github.com/bjohare))
- Fix \#543: Always show logged-in user's full name or username in page … [\#549](https://github.com/Cadasta/cadasta-platform/pull/549) ([seav](https://github.com/seav))
- Footer CSS [\#547](https://github.com/Cadasta/cadasta-platform/pull/547) ([clash99](https://github.com/clash99))
- Reorganise test data setup in functional tests [\#546](https://github.com/Cadasta/cadasta-platform/pull/546) ([ian-ross](https://github.com/ian-ross))
- Address XForms Technical Debt [\#545](https://github.com/Cadasta/cadasta-platform/pull/545) ([bjohare](https://github.com/bjohare))
- Try to make functional tests more reliable [\#544](https://github.com/Cadasta/cadasta-platform/pull/544) ([ian-ross](https://github.com/ian-ross))
- Resolve \#441: Improve relationship party selection widget [\#542](https://github.com/Cadasta/cadasta-platform/pull/542) ([seav](https://github.com/seav))
- Fix \#463: Make URL errors more meaningful [\#541](https://github.com/Cadasta/cadasta-platform/pull/541) ([seav](https://github.com/seav))
- Fix \#525: "Next" button is default in wizard steps [\#538](https://github.com/Cadasta/cadasta-platform/pull/538) ([ian-ross](https://github.com/ian-ross))
- Firefox for testing from S3 bucket [\#536](https://github.com/Cadasta/cadasta-platform/pull/536) ([ian-ross](https://github.com/ian-ross))
- Fix \#528: Include contacts when adding a project [\#535](https://github.com/Cadasta/cadasta-platform/pull/535) ([seav](https://github.com/seav))
- Fix \#530: add project wizard data preservation [\#534](https://github.com/Cadasta/cadasta-platform/pull/534) ([ian-ross](https://github.com/ian-ross))
- Fix \#520: ellipsis menu visibility [\#532](https://github.com/Cadasta/cadasta-platform/pull/532) ([ian-ross](https://github.com/ian-ross))
- Refactor permissions checks \(fixes \#485\) [\#531](https://github.com/Cadasta/cadasta-platform/pull/531) ([ian-ross](https://github.com/ian-ross))
- Fix \#527 [\#529](https://github.com/Cadasta/cadasta-platform/pull/529) ([seav](https://github.com/seav))
- Resolve \#324: Prevent duplicate org and project names [\#526](https://github.com/Cadasta/cadasta-platform/pull/526) ([seav](https://github.com/seav))
- Add SHP download [\#523](https://github.com/Cadasta/cadasta-platform/pull/523) ([oliverroick](https://github.com/oliverroick))
- Seav's branch changes [\#519](https://github.com/Cadasta/cadasta-platform/pull/519) ([clash99](https://github.com/clash99))
- Make OSM tile access be over HTTPS [\#518](https://github.com/Cadasta/cadasta-platform/pull/518) ([ian-ross](https://github.com/ian-ross))
- Fix \#507: Adding resources from multiple pages in the library now works [\#517](https://github.com/Cadasta/cadasta-platform/pull/517) ([seav](https://github.com/seav))
- Resolve \#295 and \#407: Improve the UI/UX in adding/uploading resources [\#516](https://github.com/Cadasta/cadasta-platform/pull/516) ([seav](https://github.com/seav))
- Page content css bug fix [\#515](https://github.com/Cadasta/cadasta-platform/pull/515) ([clash99](https://github.com/clash99))
- Improved handling of resource files [\#514](https://github.com/Cadasta/cadasta-platform/pull/514) ([oliverroick](https://github.com/oliverroick))
- Add templates for new issues and pull requests [\#513](https://github.com/Cadasta/cadasta-platform/pull/513) ([oliverroick](https://github.com/oliverroick))
- Set up to use wheelhouse for PIP packages [\#512](https://github.com/Cadasta/cadasta-platform/pull/512) ([ian-ross](https://github.com/ian-ross))
- Location buttons [\#511](https://github.com/Cadasta/cadasta-platform/pull/511) ([clash99](https://github.com/clash99))
- Fix \#406 and \#325 [\#509](https://github.com/Cadasta/cadasta-platform/pull/509) ([seav](https://github.com/seav))
- Datatable formatting [\#508](https://github.com/Cadasta/cadasta-platform/pull/508) ([clash99](https://github.com/clash99))
- Remove main.css.map from repo and ignore from now on [\#506](https://github.com/Cadasta/cadasta-platform/pull/506) ([oliverroick](https://github.com/oliverroick))
- Fix \#476 and \#364: Improve contacts form UI [\#505](https://github.com/Cadasta/cadasta-platform/pull/505) ([seav](https://github.com/seav))
- Wizard steps [\#504](https://github.com/Cadasta/cadasta-platform/pull/504) ([clash99](https://github.com/clash99))
- Add support for Django debug toolbar [\#501](https://github.com/Cadasta/cadasta-platform/pull/501) ([ian-ross](https://github.com/ian-ross))
- Data download css updates [\#500](https://github.com/Cadasta/cadasta-platform/pull/500) ([clash99](https://github.com/clash99))
- Fix user-based UI element visibility issues [\#499](https://github.com/Cadasta/cadasta-platform/pull/499) ([ian-ross](https://github.com/ian-ross))
- Checkbox focus css fix [\#491](https://github.com/Cadasta/cadasta-platform/pull/491) ([clash99](https://github.com/clash99))
- Fix \#134: DRF docs and API versions [\#484](https://github.com/Cadasta/cadasta-platform/pull/484) ([ian-ross](https://github.com/ian-ross))
- Improvements to file upload post processing [\#483](https://github.com/Cadasta/cadasta-platform/pull/483) ([oliverroick](https://github.com/oliverroick))
- More aggressive Squid caching for external URLs [\#482](https://github.com/Cadasta/cadasta-platform/pull/482) ([ian-ross](https://github.com/ian-ross))
- Resolve \#427: Don't display empty resources table for locations [\#477](https://github.com/Cadasta/cadasta-platform/pull/477) ([seav](https://github.com/seav))
- Css fix for long title and stats css [\#475](https://github.com/Cadasta/cadasta-platform/pull/475) ([clash99](https://github.com/clash99))
- Fixes \#397 -- Adds custom required message to LocationForm [\#473](https://github.com/Cadasta/cadasta-platform/pull/473) ([oliverroick](https://github.com/oliverroick))
- Fixes \#315 -- Set \_errors when contact is removed [\#472](https://github.com/Cadasta/cadasta-platform/pull/472) ([oliverroick](https://github.com/oliverroick))
- Fix \#414: Remove unnecessary slugify\(\) call [\#470](https://github.com/Cadasta/cadasta-platform/pull/470) ([seav](https://github.com/seav))
- Hamburger menu conditional users [\#469](https://github.com/Cadasta/cadasta-platform/pull/469) ([clash99](https://github.com/clash99))
- Fix \#457: Remove randomness from functional tests [\#467](https://github.com/Cadasta/cadasta-platform/pull/467) ([seav](https://github.com/seav))
- Resources modal width, Messaging update [\#459](https://github.com/Cadasta/cadasta-platform/pull/459) ([clash99](https://github.com/clash99))
- Fix \#452: user menu visibility [\#458](https://github.com/Cadasta/cadasta-platform/pull/458) ([ian-ross](https://github.com/ian-ross))
- Quick fix for functional test [\#456](https://github.com/Cadasta/cadasta-platform/pull/456) ([ian-ross](https://github.com/ian-ross))
- Relationship modal, scrollbar bug fix, hide org logo [\#455](https://github.com/Cadasta/cadasta-platform/pull/455) ([clash99](https://github.com/clash99))

## [v0.1.0](https://github.com/Cadasta/cadasta-platform/tree/v0.1.0) (2016-07-14)
[Full Changelog](https://github.com/Cadasta/cadasta-platform/compare/last-with-react...v0.1.0)

**Implemented enhancements:**

- Improve Map Tip [\#401](https://github.com/Cadasta/cadasta-platform/issues/401)
- Project User Permissions Needs Mobile Optimization [\#341](https://github.com/Cadasta/cadasta-platform/issues/341)
- Map should zoom to project extend when adding first location [\#338](https://github.com/Cadasta/cadasta-platform/issues/338)
- Project overview starter text displays always [\#319](https://github.com/Cadasta/cadasta-platform/issues/319)
- Refine zoom of world view for creation of project geometry [\#313](https://github.com/Cadasta/cadasta-platform/issues/313)
- Increase Allowed maxZoom for Basemaps [\#311](https://github.com/Cadasta/cadasta-platform/issues/311)
- Location details - Empty resource and relationship starter text [\#300](https://github.com/Cadasta/cadasta-platform/issues/300)
- Add gif to acceptable resource file types [\#279](https://github.com/Cadasta/cadasta-platform/issues/279)
- Zoom map to project extent [\#276](https://github.com/Cadasta/cadasta-platform/issues/276)
- Add geospatial search API for locations \(spatial units\) [\#238](https://github.com/Cadasta/cadasta-platform/issues/238)
- GeoODK/ODK Integration [\#219](https://github.com/Cadasta/cadasta-platform/issues/219)
- Only show the link for the Users list page to SUs [\#205](https://github.com/Cadasta/cadasta-platform/issues/205)
- The HTML \<title\> of add/edit project pages should be more specific [\#198](https://github.com/Cadasta/cadasta-platform/issues/198)
- Label for the questionnaire form field refers to the URL form field [\#197](https://github.com/Cadasta/cadasta-platform/issues/197)
- Make the org logo in the project page a link to the organization's page [\#182](https://github.com/Cadasta/cadasta-platform/issues/182)
- Design CSS for Wizard pages [\#174](https://github.com/Cadasta/cadasta-platform/issues/174)
- Improve user error messaging consistency for forms [\#59](https://github.com/Cadasta/cadasta-platform/issues/59)

**Fixed bugs:**

- Resolver for URLs with usernames do not include all valid characters [\#439](https://github.com/Cadasta/cadasta-platform/issues/439)
- Investigate discrepancies in questionnaires table [\#433](https://github.com/Cadasta/cadasta-platform/issues/433)
- Geoshape comes across as a polyline [\#430](https://github.com/Cadasta/cadasta-platform/issues/430)
- Can't add new location \(name issue\) [\#426](https://github.com/Cadasta/cadasta-platform/issues/426)
- S3 Files that begin with a number causing issues for pyxforms [\#420](https://github.com/Cadasta/cadasta-platform/issues/420)
- Registration page background not covering page [\#418](https://github.com/Cadasta/cadasta-platform/issues/418)
- Can't Download ODK Form from Staging [\#417](https://github.com/Cadasta/cadasta-platform/issues/417)
- Updating profile causes glitch in permissions [\#416](https://github.com/Cadasta/cadasta-platform/issues/416)
- JavaScript Error on Map Tab Load [\#402](https://github.com/Cadasta/cadasta-platform/issues/402)
- Unable to add member within Organization overview window [\#394](https://github.com/Cadasta/cadasta-platform/issues/394)
- Unable to add resource from library to new location [\#393](https://github.com/Cadasta/cadasta-platform/issues/393)
- Tenure type selection not available when adding relationship to a new location [\#392](https://github.com/Cadasta/cadasta-platform/issues/392)
- TenureRelationship model should have a 'acquired\_how' field [\#386](https://github.com/Cadasta/cadasta-platform/issues/386)
- Extra "testing" field in add location [\#381](https://github.com/Cadasta/cadasta-platform/issues/381)
- Location view should zoom to the extent of the geometry [\#377](https://github.com/Cadasta/cadasta-platform/issues/377)
- Limit questionnaire file type [\#374](https://github.com/Cadasta/cadasta-platform/issues/374)
- Redirecting error & mass messages appear [\#369](https://github.com/Cadasta/cadasta-platform/issues/369)
- Form Submission Will Not Parse [\#366](https://github.com/Cadasta/cadasta-platform/issues/366)
- Consistent Error Messaging on Add Location [\#365](https://github.com/Cadasta/cadasta-platform/issues/365)
- Dead images on Project Listview [\#363](https://github.com/Cadasta/cadasta-platform/issues/363)
- Add New Members Button Doesn't work from Org Overview Page [\#362](https://github.com/Cadasta/cadasta-platform/issues/362)
- Remove Link to Org Logo from Org Overview Page [\#361](https://github.com/Cadasta/cadasta-platform/issues/361)
- S3 resources unable to upload [\#347](https://github.com/Cadasta/cadasta-platform/issues/347)
- Email Templates Not Complete [\#346](https://github.com/Cadasta/cadasta-platform/issues/346)
- Revise Export Text [\#342](https://github.com/Cadasta/cadasta-platform/issues/342)
- Demo Site Deployment Bugs [\#337](https://github.com/Cadasta/cadasta-platform/issues/337)
- Can't upload image resources when S3 Storage is active [\#334](https://github.com/Cadasta/cadasta-platform/issues/334)
- Locations west of 180°W or east of 180°E can be added [\#332](https://github.com/Cadasta/cadasta-platform/issues/332)
- Use username in header if full name is empty [\#331](https://github.com/Cadasta/cadasta-platform/issues/331)
- Organization or project names longer than 50 characters result in DataError [\#328](https://github.com/Cadasta/cadasta-platform/issues/328)
- Non-ASCII organization and project names will crash the website [\#327](https://github.com/Cadasta/cadasta-platform/issues/327)
- 500 Error When Registering Username on Staging [\#310](https://github.com/Cadasta/cadasta-platform/issues/310)
- Cannot Add Resources to Location [\#303](https://github.com/Cadasta/cadasta-platform/issues/303)
- xlsform does not parse [\#302](https://github.com/Cadasta/cadasta-platform/issues/302)
- Private/Public Slider & Text Mushed Together on Project Details Page on Mobile [\#297](https://github.com/Cadasta/cadasta-platform/issues/297)
- Attributes schemas should be associated with a questionnaire [\#291](https://github.com/Cadasta/cadasta-platform/issues/291)
- An organization or  a project with the slug 'new' or a user with the username 'add' will conflict with the add functions [\#285](https://github.com/Cadasta/cadasta-platform/issues/285)
- Edit resource  [\#282](https://github.com/Cadasta/cadasta-platform/issues/282)
- Adding duplicate org member throws error [\#263](https://github.com/Cadasta/cadasta-platform/issues/263)
- Roboto font not importing correctly [\#260](https://github.com/Cadasta/cadasta-platform/issues/260)
- Edit project location leads to a blank page [\#247](https://github.com/Cadasta/cadasta-platform/issues/247)
- Add Button for new organization is not visible [\#243](https://github.com/Cadasta/cadasta-platform/issues/243)
- Cannot Add New Resource [\#240](https://github.com/Cadasta/cadasta-platform/issues/240)
- TenureRelationship has unnecessary fields [\#227](https://github.com/Cadasta/cadasta-platform/issues/227)
- TenureRelationship is missing the project field [\#226](https://github.com/Cadasta/cadasta-platform/issues/226)
- Relationship models should only relate entities from the same project [\#225](https://github.com/Cadasta/cadasta-platform/issues/225)
- Dashboard map not centered over points being displayed [\#213](https://github.com/Cadasta/cadasta-platform/issues/213)
- Page footer is no longer fixed to the bottom of the viewport [\#206](https://github.com/Cadasta/cadasta-platform/issues/206)
- Private projects are still shown on the Dashboard map [\#196](https://github.com/Cadasta/cadasta-platform/issues/196)
- Weird form bugs when adding a project and the project name is missing [\#195](https://github.com/Cadasta/cadasta-platform/issues/195)
- Save/Cancel buttons are not fully visible when editing the project details or permissions [\#194](https://github.com/Cadasta/cadasta-platform/issues/194)
- Logged out users are not able to see any public organizations and projects [\#188](https://github.com/Cadasta/cadasta-platform/issues/188)
- Dashboard map and create project geometry map controls have wrong z-index [\#186](https://github.com/Cadasta/cadasta-platform/issues/186)
- Private projects are not visible to superusers [\#179](https://github.com/Cadasta/cadasta-platform/issues/179)
- UserListTest sometimes throws error [\#175](https://github.com/Cadasta/cadasta-platform/issues/175)
- Check if project-slug exists when creating a project [\#162](https://github.com/Cadasta/cadasta-platform/issues/162)
- Set country on project creation [\#144](https://github.com/Cadasta/cadasta-platform/issues/144)
- Error message display over dashboard map [\#140](https://github.com/Cadasta/cadasta-platform/issues/140)
- User model should have "full name" not "first name, last name" [\#98](https://github.com/Cadasta/cadasta-platform/issues/98)

**Closed issues:**

- VM provisioning is broken [\#395](https://github.com/Cadasta/cadasta-platform/issues/395)
- example.com still in the subject of email to users [\#387](https://github.com/Cadasta/cadasta-platform/issues/387)
- Cannot add resources to location [\#367](https://github.com/Cadasta/cadasta-platform/issues/367)
- If the organization or project name changes, should the slug change as well? [\#329](https://github.com/Cadasta/cadasta-platform/issues/329)
- Add Organization dialog box not fully visible and no scroll bar option [\#314](https://github.com/Cadasta/cadasta-platform/issues/314)
- Need error message on add new location [\#309](https://github.com/Cadasta/cadasta-platform/issues/309)
- Add project permission denied after step 3 [\#307](https://github.com/Cadasta/cadasta-platform/issues/307)
- CSS "cursor" should be "pointer" for table rows that act as links [\#306](https://github.com/Cadasta/cadasta-platform/issues/306)
- Swap "Entities associated" header column [\#301](https://github.com/Cadasta/cadasta-platform/issues/301)
- CSS for new location wizard [\#294](https://github.com/Cadasta/cadasta-platform/issues/294)
- Can't download resources [\#281](https://github.com/Cadasta/cadasta-platform/issues/281)
- Typo in error message [\#280](https://github.com/Cadasta/cadasta-platform/issues/280)
- Resource description field - not required [\#278](https://github.com/Cadasta/cadasta-platform/issues/278)
- Initial release - hide components [\#271](https://github.com/Cadasta/cadasta-platform/issues/271)
- CSS for Resource components [\#264](https://github.com/Cadasta/cadasta-platform/issues/264)
- Improve instruction/error messaging around urls [\#259](https://github.com/Cadasta/cadasta-platform/issues/259)
- Entity Attributes Data Model Part 2 [\#255](https://github.com/Cadasta/cadasta-platform/issues/255)
- Responsive layout needs fix [\#250](https://github.com/Cadasta/cadasta-platform/issues/250)
- Audit logging [\#244](https://github.com/Cadasta/cadasta-platform/issues/244)
- Button to make organization private still visible. [\#237](https://github.com/Cadasta/cadasta-platform/issues/237)
- Creation of Project Records Attribute Schema [\#235](https://github.com/Cadasta/cadasta-platform/issues/235)
- Design CSS for Wizard pages [\#231](https://github.com/Cadasta/cadasta-platform/issues/231)
- Message placement on single org/project pages [\#229](https://github.com/Cadasta/cadasta-platform/issues/229)
- Fix pagination when there is only one page [\#228](https://github.com/Cadasta/cadasta-platform/issues/228)
- Edit organization modal not saving or redirecting back to organization dashboard [\#222](https://github.com/Cadasta/cadasta-platform/issues/222)
- Data Downloads [\#220](https://github.com/Cadasta/cadasta-platform/issues/220)
- Update icon on tab for CKAN platform [\#201](https://github.com/Cadasta/cadasta-platform/issues/201)
- CSS for Smaller Screens [\#200](https://github.com/Cadasta/cadasta-platform/issues/200)
- Update header ui [\#193](https://github.com/Cadasta/cadasta-platform/issues/193)
- Alt attribute of the organization's logo should be the organization's name [\#191](https://github.com/Cadasta/cadasta-platform/issues/191)
- Project model's `project\_slug` field should not have `null=True` [\#180](https://github.com/Cadasta/cadasta-platform/issues/180)
- Spatial unit data modelling and API [\#177](https://github.com/Cadasta/cadasta-platform/issues/177)
- Records [\#172](https://github.com/Cadasta/cadasta-platform/issues/172)
- Records UI Views [\#171](https://github.com/Cadasta/cadasta-platform/issues/171)
- Records API views/serialisers [\#170](https://github.com/Cadasta/cadasta-platform/issues/170)
- Records API Design [\#169](https://github.com/Cadasta/cadasta-platform/issues/169)
- Records Data Modeling [\#167](https://github.com/Cadasta/cadasta-platform/issues/167)
- Time success message [\#165](https://github.com/Cadasta/cadasta-platform/issues/165)
- New template wrapper for organizations [\#164](https://github.com/Cadasta/cadasta-platform/issues/164)
- New template wrapper for projects [\#163](https://github.com/Cadasta/cadasta-platform/issues/163)
- tox error [\#161](https://github.com/Cadasta/cadasta-platform/issues/161)
- CSS for Modals [\#156](https://github.com/Cadasta/cadasta-platform/issues/156)
- `vagrant up` fails with npm error [\#150](https://github.com/Cadasta/cadasta-platform/issues/150)
- Contacts for organizations and projects [\#136](https://github.com/Cadasta/cadasta-platform/issues/136)
- Permissions for organizations UI [\#135](https://github.com/Cadasta/cadasta-platform/issues/135)
- Clean-up Tasks - Ian [\#132](https://github.com/Cadasta/cadasta-platform/issues/132)
- Entity Attributes Data Model Part 1 [\#131](https://github.com/Cadasta/cadasta-platform/issues/131)
- Resources [\#130](https://github.com/Cadasta/cadasta-platform/issues/130)
- XLSForm Parsing and Upload [\#129](https://github.com/Cadasta/cadasta-platform/issues/129)
- Design CSS [\#118](https://github.com/Cadasta/cadasta-platform/issues/118)
- Code layout and VM setup tidying [\#117](https://github.com/Cadasta/cadasta-platform/issues/117)
- Projects UI implementation: Part 2 [\#116](https://github.com/Cadasta/cadasta-platform/issues/116)
- Set up translations and connect to Transifex [\#115](https://github.com/Cadasta/cadasta-platform/issues/115)
- Functional testing for projects pages [\#114](https://github.com/Cadasta/cadasta-platform/issues/114)
- Functional testing for organization members pages [\#113](https://github.com/Cadasta/cadasta-platform/issues/113)
- Functional testing for organization pages [\#112](https://github.com/Cadasta/cadasta-platform/issues/112)
- Functional testing for user management pages [\#111](https://github.com/Cadasta/cadasta-platform/issues/111)
- Sprint \#3 functional testing [\#96](https://github.com/Cadasta/cadasta-platform/issues/96)
- UI for resource management [\#95](https://github.com/Cadasta/cadasta-platform/issues/95)
- UI for projects [\#94](https://github.com/Cadasta/cadasta-platform/issues/94)
- Projects UI implementation: Part 1 [\#93](https://github.com/Cadasta/cadasta-platform/issues/93)
- Organization members UI implementation [\#92](https://github.com/Cadasta/cadasta-platform/issues/92)
- Organization UI implementation [\#91](https://github.com/Cadasta/cadasta-platform/issues/91)
- User management UI implementation [\#90](https://github.com/Cadasta/cadasta-platform/issues/90)
- API Docs [\#84](https://github.com/Cadasta/cadasta-platform/issues/84)
- Create Test Data Fixtures [\#83](https://github.com/Cadasta/cadasta-platform/issues/83)
- Resource serializer [\#70](https://github.com/Cadasta/cadasta-platform/issues/70)
- UI for Resource Management [\#69](https://github.com/Cadasta/cadasta-platform/issues/69)
- Permissions for resources [\#68](https://github.com/Cadasta/cadasta-platform/issues/68)
- Resource API Views [\#67](https://github.com/Cadasta/cadasta-platform/issues/67)
- Design Resource API [\#66](https://github.com/Cadasta/cadasta-platform/issues/66)
- Resource model [\#65](https://github.com/Cadasta/cadasta-platform/issues/65)
- UI for Organizations [\#52](https://github.com/Cadasta/cadasta-platform/issues/52)
- Project API views [\#39](https://github.com/Cadasta/cadasta-platform/issues/39)
- Project visibility control [\#37](https://github.com/Cadasta/cadasta-platform/issues/37)
- UI for User Management [\#31](https://github.com/Cadasta/cadasta-platform/issues/31)
- API for assignment of roles to users [\#29](https://github.com/Cadasta/cadasta-platform/issues/29)
- archiving [\#27](https://github.com/Cadasta/cadasta-platform/issues/27)
- Editable polygons on map [\#25](https://github.com/Cadasta/cadasta-platform/issues/25)
- Slippy Map [\#24](https://github.com/Cadasta/cadasta-platform/issues/24)
- Create and Edit Forms [\#22](https://github.com/Cadasta/cadasta-platform/issues/22)
- Archive/delete workflows [\#21](https://github.com/Cadasta/cadasta-platform/issues/21)
- Questionnaire data [\#17](https://github.com/Cadasta/cadasta-platform/issues/17)
- Map [\#14](https://github.com/Cadasta/cadasta-platform/issues/14)
- Relationships [\#13](https://github.com/Cadasta/cadasta-platform/issues/13)
- Parties [\#12](https://github.com/Cadasta/cadasta-platform/issues/12)
- Parcels [\#11](https://github.com/Cadasta/cadasta-platform/issues/11)
- Projects [\#10](https://github.com/Cadasta/cadasta-platform/issues/10)
- Organisations [\#9](https://github.com/Cadasta/cadasta-platform/issues/9)

**Merged pull requests:**

- Fix \#439: characters in usernames in URLs [\#444](https://github.com/Cadasta/cadasta-platform/pull/444) ([ian-ross](https://github.com/ian-ross))
- Fixed bg image by adding body class [\#438](https://github.com/Cadasta/cadasta-platform/pull/438) ([clash99](https://github.com/clash99))
- XForm attributes are now loaded properly [\#437](https://github.com/Cadasta/cadasta-platform/pull/437) ([linzjax](https://github.com/linzjax))
- Geoshape glitch work around. [\#435](https://github.com/Cadasta/cadasta-platform/pull/435) ([linzjax](https://github.com/linzjax))
- Fixes \#430 [\#431](https://github.com/Cadasta/cadasta-platform/pull/431) ([linzjax](https://github.com/linzjax))
- Fix superuser behaviour for add project wizard [\#428](https://github.com/Cadasta/cadasta-platform/pull/428) ([ian-ross](https://github.com/ian-ross))
- Adds AWS S3 bucket support [\#425](https://github.com/Cadasta/cadasta-platform/pull/425) ([amplifi](https://github.com/amplifi))
- Improve upload handling of resources [\#424](https://github.com/Cadasta/cadasta-platform/pull/424) ([oliverroick](https://github.com/oliverroick))
- Fixes \#417 -- Fixes naming of form download URLs [\#423](https://github.com/Cadasta/cadasta-platform/pull/423) ([oliverroick](https://github.com/oliverroick))
- Suppress missing logo [\#422](https://github.com/Cadasta/cadasta-platform/pull/422) ([ian-ross](https://github.com/ian-ross))
- Bump buckets version to fix \#420 [\#421](https://github.com/Cadasta/cadasta-platform/pull/421) ([ian-ross](https://github.com/ian-ross))
- Resource fix [\#419](https://github.com/Cadasta/cadasta-platform/pull/419) ([clash99](https://github.com/clash99))
- removed location name from model and updated geoodk api [\#415](https://github.com/Cadasta/cadasta-platform/pull/415) ([linzjax](https://github.com/linzjax))
- Fix the Unicode! [\#413](https://github.com/Cadasta/cadasta-platform/pull/413) ([ian-ross](https://github.com/ian-ross))
- Location details right panel [\#411](https://github.com/Cadasta/cadasta-platform/pull/411) ([clash99](https://github.com/clash99))
- Attempt to fix \#393 -- GeoJSON added to template context on LocationR… [\#410](https://github.com/Cadasta/cadasta-platform/pull/410) ([oliverroick](https://github.com/oliverroick))
- Fixes \#402 -- Zoom to locations only when project has locations [\#408](https://github.com/Cadasta/cadasta-platform/pull/408) ([oliverroick](https://github.com/oliverroick))
- Fix 'is\_superuser' errors in views [\#404](https://github.com/Cadasta/cadasta-platform/pull/404) ([ian-ross](https://github.com/ian-ross))
- Fixes \#369 — Fixes permission denied redirects [\#400](https://github.com/Cadasta/cadasta-platform/pull/400) ([oliverroick](https://github.com/oliverroick))
- Map error message [\#399](https://github.com/Cadasta/cadasta-platform/pull/399) ([clash99](https://github.com/clash99))
- Fix \#395: tidy up static data loading [\#398](https://github.com/Cadasta/cadasta-platform/pull/398) ([ian-ross](https://github.com/ian-ross))
- Improve map display [\#396](https://github.com/Cadasta/cadasta-platform/pull/396) ([oliverroick](https://github.com/oliverroick))
- Fix \#331: display user name if no full name [\#391](https://github.com/Cadasta/cadasta-platform/pull/391) ([ian-ross](https://github.com/ian-ross))
- Fixes \#387: new command to replace default site object [\#390](https://github.com/Cadasta/cadasta-platform/pull/390) ([linzjax](https://github.com/linzjax))
- Fixes \#341 [\#388](https://github.com/Cadasta/cadasta-platform/pull/388) ([linzjax](https://github.com/linzjax))
- Fixes \#276 and \#377 [\#385](https://github.com/Cadasta/cadasta-platform/pull/385) ([seav](https://github.com/seav))
- Fixes 333 and Fixes 332 \(temporarily\) [\#382](https://github.com/Cadasta/cadasta-platform/pull/382) ([linzjax](https://github.com/linzjax))
- Fix \#361: organization logo visibility [\#380](https://github.com/Cadasta/cadasta-platform/pull/380) ([ian-ross](https://github.com/ian-ross))
- Fix creating locations when no form has been uploaded [\#379](https://github.com/Cadasta/cadasta-platform/pull/379) ([oliverroick](https://github.com/oliverroick))
- Fixes \#374 -- Check mime type of uploaded file [\#378](https://github.com/Cadasta/cadasta-platform/pull/378) ([oliverroick](https://github.com/oliverroick))
- Adds JOSN  attributes to UI [\#375](https://github.com/Cadasta/cadasta-platform/pull/375) ([oliverroick](https://github.com/oliverroick))
- Added message timing and css [\#373](https://github.com/Cadasta/cadasta-platform/pull/373) ([clash99](https://github.com/clash99))
- Added xforms api for integration with GeoODK [\#370](https://github.com/Cadasta/cadasta-platform/pull/370) ([linzjax](https://github.com/linzjax))
- CSS for error msgs [\#360](https://github.com/Cadasta/cadasta-platform/pull/360) ([linzjax](https://github.com/linzjax))
- Fixes \#346 -- Clean email templates [\#359](https://github.com/Cadasta/cadasta-platform/pull/359) ([oliverroick](https://github.com/oliverroick))
- Fix \#328: Slug length control with custom slugify [\#356](https://github.com/Cadasta/cadasta-platform/pull/356) ([ian-ross](https://github.com/ian-ross))
- Bugfix/messages [\#353](https://github.com/Cadasta/cadasta-platform/pull/353) ([oliverroick](https://github.com/oliverroick))
- Fix for \#205: "Users" menu visibility [\#352](https://github.com/Cadasta/cadasta-platform/pull/352) ([ian-ross](https://github.com/ian-ross))
- Fixes \#347 [\#351](https://github.com/Cadasta/cadasta-platform/pull/351) ([oliverroick](https://github.com/oliverroick))
- Fix \#327: Allow Unicode slugs [\#349](https://github.com/Cadasta/cadasta-platform/pull/349) ([seav](https://github.com/seav))
- Provisioning and deployment updates [\#348](https://github.com/Cadasta/cadasta-platform/pull/348) ([amplifi](https://github.com/amplifi))
- Fix permissions policies and tests \(fixes \#303\) [\#336](https://github.com/Cadasta/cadasta-platform/pull/336) ([ian-ross](https://github.com/ian-ross))
- Adds data download [\#335](https://github.com/Cadasta/cadasta-platform/pull/335) ([oliverroick](https://github.com/oliverroick))
- Fixes \#319 [\#330](https://github.com/Cadasta/cadasta-platform/pull/330) ([seav](https://github.com/seav))
- Test + production URL configs [\#326](https://github.com/Cadasta/cadasta-platform/pull/326) ([oliverroick](https://github.com/oliverroick))
- Organization page titles [\#321](https://github.com/Cadasta/cadasta-platform/pull/321) ([clash99](https://github.com/clash99))
- Add support for conditional attributes [\#320](https://github.com/Cadasta/cadasta-platform/pull/320) ([bjohare](https://github.com/bjohare))
- Add records API URL unit tests [\#318](https://github.com/Cadasta/cadasta-platform/pull/318) ([seav](https://github.com/seav))
- Fixes \#285 [\#317](https://github.com/Cadasta/cadasta-platform/pull/317) ([seav](https://github.com/seav))
- Fixes \#311 [\#312](https://github.com/Cadasta/cadasta-platform/pull/312) ([seav](https://github.com/seav))
- Location Wizard CSS and small css fixes [\#308](https://github.com/Cadasta/cadasta-platform/pull/308) ([clash99](https://github.com/clash99))
- Fixes \#279 [\#305](https://github.com/Cadasta/cadasta-platform/pull/305) ([seav](https://github.com/seav))
- Resources bugfixes [\#304](https://github.com/Cadasta/cadasta-platform/pull/304) ([oliverroick](https://github.com/oliverroick))
- Hiding elements for beta [\#298](https://github.com/Cadasta/cadasta-platform/pull/298) ([clash99](https://github.com/clash99))
- Add missing URL in menu item [\#293](https://github.com/Cadasta/cadasta-platform/pull/293) ([seav](https://github.com/seav))
- Fix for \#291 [\#292](https://github.com/Cadasta/cadasta-platform/pull/292) ([bjohare](https://github.com/bjohare))
- Fixes \#227 [\#290](https://github.com/Cadasta/cadasta-platform/pull/290) ([seav](https://github.com/seav))
- fix bad merge [\#289](https://github.com/Cadasta/cadasta-platform/pull/289) ([wonderchook](https://github.com/wonderchook))
- CSS for resources area at project level [\#288](https://github.com/Cadasta/cadasta-platform/pull/288) ([clash99](https://github.com/clash99))
- Adds records UI [\#287](https://github.com/Cadasta/cadasta-platform/pull/287) ([oliverroick](https://github.com/oliverroick))
- Fixes \#263 [\#286](https://github.com/Cadasta/cadasta-platform/pull/286) ([seav](https://github.com/seav))
- Project Wizard CSS [\#277](https://github.com/Cadasta/cadasta-platform/pull/277) ([clash99](https://github.com/clash99))
- Update missing footer links [\#275](https://github.com/Cadasta/cadasta-platform/pull/275) ([clash99](https://github.com/clash99))
- Complete and improve records API [\#270](https://github.com/Cadasta/cadasta-platform/pull/270) ([seav](https://github.com/seav))
- Add support for Record Attribute Schemas [\#268](https://github.com/Cadasta/cadasta-platform/pull/268) ([bjohare](https://github.com/bjohare))
- CSS for modals [\#267](https://github.com/Cadasta/cadasta-platform/pull/267) ([clash99](https://github.com/clash99))
- CSS Responsive Layout [\#265](https://github.com/Cadasta/cadasta-platform/pull/265) ([clash99](https://github.com/clash99))
- Fixes \#213: Points are now centered on the map. [\#262](https://github.com/Cadasta/cadasta-platform/pull/262) ([linzjax](https://github.com/linzjax))
- Css for 3 project edit pages [\#256](https://github.com/Cadasta/cadasta-platform/pull/256) ([clash99](https://github.com/clash99))
- Project edit details form css [\#253](https://github.com/Cadasta/cadasta-platform/pull/253) ([clash99](https://github.com/clash99))
- Add conditional paging for datatables [\#252](https://github.com/Cadasta/cadasta-platform/pull/252) ([ian-ross](https://github.com/ian-ross))
- Add audit logging using simple-history package [\#251](https://github.com/Cadasta/cadasta-platform/pull/251) ([ian-ross](https://github.com/ian-ross))
- Fixes \#240 + \#247 -- Adapt templates to new project wrapper [\#248](https://github.com/Cadasta/cadasta-platform/pull/248) ([oliverroick](https://github.com/oliverroick))
- Public organizations and projects are now visible to all users [\#246](https://github.com/Cadasta/cadasta-platform/pull/246) ([linzjax](https://github.com/linzjax))
- remove reference to PhantomJS [\#241](https://github.com/Cadasta/cadasta-platform/pull/241) ([wonderchook](https://github.com/wonderchook))
- Downgrade to Firefox 46 for functional testing [\#239](https://github.com/Cadasta/cadasta-platform/pull/239) ([ian-ross](https://github.com/ian-ross))
- Add project constraint check when creating relationships [\#236](https://github.com/Cadasta/cadasta-platform/pull/236) ([bjohare](https://github.com/bjohare))
- Applied design css for blue scheme [\#234](https://github.com/Cadasta/cadasta-platform/pull/234) ([linzjax](https://github.com/linzjax))
- Fix \#226: TenureRelationship is missing the project field [\#232](https://github.com/Cadasta/cadasta-platform/pull/232) ([bjohare](https://github.com/bjohare))
- Functional tests for projects UI [\#224](https://github.com/Cadasta/cadasta-platform/pull/224) ([ian-ross](https://github.com/ian-ross))
- Added wrapper to organization templates [\#223](https://github.com/Cadasta/cadasta-platform/pull/223) ([linzjax](https://github.com/linzjax))
- Fix \#162 -- Always verify slug when object is created [\#221](https://github.com/Cadasta/cadasta-platform/pull/221) ([oliverroick](https://github.com/oliverroick))
- Text changes on account pages [\#218](https://github.com/Cadasta/cadasta-platform/pull/218) ([clash99](https://github.com/clash99))
- Dashboard map css [\#217](https://github.com/Cadasta/cadasta-platform/pull/217) ([clash99](https://github.com/clash99))
- Delete unnecessary file [\#216](https://github.com/Cadasta/cadasta-platform/pull/216) ([seav](https://github.com/seav))
- Add support for tenure relationships [\#215](https://github.com/Cadasta/cadasta-platform/pull/215) ([bjohare](https://github.com/bjohare))
- Fixes \#196: Private projects only visible to organization members  [\#214](https://github.com/Cadasta/cadasta-platform/pull/214) ([linzjax](https://github.com/linzjax))
- Fix \#175 -- Removes dependency on code from inside the view and ensur… [\#212](https://github.com/Cadasta/cadasta-platform/pull/212) ([ian-ross](https://github.com/ian-ross))
- Add resource Django app [\#211](https://github.com/Cadasta/cadasta-platform/pull/211) ([oliverroick](https://github.com/oliverroick))
- Initial implementation of Party API [\#210](https://github.com/Cadasta/cadasta-platform/pull/210) ([bjohare](https://github.com/bjohare))
- Spatial unit model, api design, implimentation and tests [\#209](https://github.com/Cadasta/cadasta-platform/pull/209) ([linzjax](https://github.com/linzjax))
- Bugfix -- Delete all contacts [\#207](https://github.com/Cadasta/cadasta-platform/pull/207) ([oliverroick](https://github.com/oliverroick))
- Fix \#195 -- Correct display of project forms [\#204](https://github.com/Cadasta/cadasta-platform/pull/204) ([oliverroick](https://github.com/oliverroick))
- Fix \#197 -- Correct use of label ID [\#203](https://github.com/Cadasta/cadasta-platform/pull/203) ([oliverroick](https://github.com/oliverroick))
- Contacts form for organizations and projects [\#202](https://github.com/Cadasta/cadasta-platform/pull/202) ([oliverroick](https://github.com/oliverroick))
- Header css [\#199](https://github.com/Cadasta/cadasta-platform/pull/199) ([clash99](https://github.com/clash99))
- Fix \#191 [\#192](https://github.com/Cadasta/cadasta-platform/pull/192) ([oliverroick](https://github.com/oliverroick))
- Squid setup for functional testing [\#190](https://github.com/Cadasta/cadasta-platform/pull/190) ([ian-ross](https://github.com/ian-ross))
- Adds Project Edit UI [\#189](https://github.com/Cadasta/cadasta-platform/pull/189) ([oliverroick](https://github.com/oliverroick))
- Fixes \#162: Add SlugModel [\#181](https://github.com/Cadasta/cadasta-platform/pull/181) ([oliverroick](https://github.com/oliverroick))
- Replace first\_name/last\_name with full\_name [\#178](https://github.com/Cadasta/cadasta-platform/pull/178) ([ian-ross](https://github.com/ian-ross))
- XLSForm upload and parsing [\#176](https://github.com/Cadasta/cadasta-platform/pull/176) ([oliverroick](https://github.com/oliverroick))
- Completed refactoring of functional tests [\#173](https://github.com/Cadasta/cadasta-platform/pull/173) ([linzjax](https://github.com/linzjax))
- New project wrapper template [\#166](https://github.com/Cadasta/cadasta-platform/pull/166) ([clash99](https://github.com/clash99))
- UI CSS changes to button and org members [\#160](https://github.com/Cadasta/cadasta-platform/pull/160) ([clash99](https://github.com/clash99))
- Fix typo [\#159](https://github.com/Cadasta/cadasta-platform/pull/159) ([oliverroick](https://github.com/oliverroick))
- Switch to Natural Earth country dataset [\#158](https://github.com/Cadasta/cadasta-platform/pull/158) ([ian-ross](https://github.com/ian-ross))
- Remove redundant setup in .travis.yml [\#155](https://github.com/Cadasta/cadasta-platform/pull/155) ([ian-ross](https://github.com/ian-ross))
- CSS for Org and Project Lists and Dashboards [\#154](https://github.com/Cadasta/cadasta-platform/pull/154) ([linzjax](https://github.com/linzjax))
- Bugs: new users default policy; org creation [\#153](https://github.com/Cadasta/cadasta-platform/pull/153) ([ian-ross](https://github.com/ian-ross))
- Project visibility control [\#151](https://github.com/Cadasta/cadasta-platform/pull/151) ([ian-ross](https://github.com/ian-ross))
- Project country determination [\#149](https://github.com/Cadasta/cadasta-platform/pull/149) ([ian-ross](https://github.com/ian-ross))
- Add initial set of users management UI functional tests [\#148](https://github.com/Cadasta/cadasta-platform/pull/148) ([seav](https://github.com/seav))
- Added functional tests for organizations list/dashboard and member [\#147](https://github.com/Cadasta/cadasta-platform/pull/147) ([linzjax](https://github.com/linzjax))
- Add Arabic language files and RTL Bootstrap CSS support [\#146](https://github.com/Cadasta/cadasta-platform/pull/146) ([ian-ross](https://github.com/ian-ross))
- Cleanup: test refactoring and test coverage [\#145](https://github.com/Cadasta/cadasta-platform/pull/145) ([ian-ross](https://github.com/ian-ross))
- Finish up project creation UI [\#143](https://github.com/Cadasta/cadasta-platform/pull/143) ([ian-ross](https://github.com/ian-ross))
- Add permissions to organization default views [\#142](https://github.com/Cadasta/cadasta-platform/pull/142) ([oliverroick](https://github.com/oliverroick))
- Cleanup round \#1 [\#141](https://github.com/Cadasta/cadasta-platform/pull/141) ([ian-ross](https://github.com/ian-ross))
- Cleaned up test data. Again. [\#138](https://github.com/Cadasta/cadasta-platform/pull/138) ([linzjax](https://github.com/linzjax))
- Adds projects map to platform dashboard [\#137](https://github.com/Cadasta/cadasta-platform/pull/137) ([oliverroick](https://github.com/oliverroick))
- Add language menu to base template [\#133](https://github.com/Cadasta/cadasta-platform/pull/133) ([ian-ross](https://github.com/ian-ross))
- Remove wizard\_state template tag [\#128](https://github.com/Cadasta/cadasta-platform/pull/128) ([ian-ross](https://github.com/ian-ross))
- Move templates to top-level directory [\#127](https://github.com/Cadasta/cadasta-platform/pull/127) ([ian-ross](https://github.com/ian-ross))
- Firefox and Xvfb for functional tests [\#126](https://github.com/Cadasta/cadasta-platform/pull/126) ([ian-ross](https://github.com/ian-ross))
- Functional test fixes [\#125](https://github.com/Cadasta/cadasta-platform/pull/125) ([ian-ross](https://github.com/ian-ross))
- Organization UI [\#124](https://github.com/Cadasta/cadasta-platform/pull/124) ([oliverroick](https://github.com/oliverroick))
- cleaned up test data [\#123](https://github.com/Cadasta/cadasta-platform/pull/123) ([linzjax](https://github.com/linzjax))
- Set up Transifex translations [\#122](https://github.com/Cadasta/cadasta-platform/pull/122) ([ian-ross](https://github.com/ian-ross))
- Upgrade to django-tutelary 0.1.10 [\#121](https://github.com/Cadasta/cadasta-platform/pull/121) ([ian-ross](https://github.com/ian-ross))
- Get all functional tests working again [\#120](https://github.com/Cadasta/cadasta-platform/pull/120) ([ian-ross](https://github.com/ian-ross))
- Remove React: switch to Django-only [\#109](https://github.com/Cadasta/cadasta-platform/pull/109) ([ian-ross](https://github.com/ian-ross))

## [last-with-react](https://github.com/Cadasta/cadasta-platform/tree/last-with-react) (2016-03-29)
**Closed issues:**

- User management API [\#89](https://github.com/Cadasta/cadasta-platform/issues/89)
- Update to new django-tutelary [\#86](https://github.com/Cadasta/cadasta-platform/issues/86)
- Ansible error [\#82](https://github.com/Cadasta/cadasta-platform/issues/82)
- UI for Search, Sort, Filtering, Pagination [\#76](https://github.com/Cadasta/cadasta-platform/issues/76)
- Functional testing setup [\#75](https://github.com/Cadasta/cadasta-platform/issues/75)
- Add platform footer [\#61](https://github.com/Cadasta/cadasta-platform/issues/61)
- Image handling in webpack [\#57](https://github.com/Cadasta/cadasta-platform/issues/57)
- User serializer [\#56](https://github.com/Cadasta/cadasta-platform/issues/56)
- Validation for contacts [\#55](https://github.com/Cadasta/cadasta-platform/issues/55)
- AWS/staging deployment [\#54](https://github.com/Cadasta/cadasta-platform/issues/54)
- UI for Base CSS [\#53](https://github.com/Cadasta/cadasta-platform/issues/53)
- UI for Users/Login/Registration [\#51](https://github.com/Cadasta/cadasta-platform/issues/51)
- Internationalisation [\#50](https://github.com/Cadasta/cadasta-platform/issues/50)
- Organization API Views [\#49](https://github.com/Cadasta/cadasta-platform/issues/49)
- Archive/Unarchive organizations [\#48](https://github.com/Cadasta/cadasta-platform/issues/48)
- Organization Serializer [\#47](https://github.com/Cadasta/cadasta-platform/issues/47)
- Design Organizations API [\#46](https://github.com/Cadasta/cadasta-platform/issues/46)
- Permissions for Organizations [\#45](https://github.com/Cadasta/cadasta-platform/issues/45)
- Organization model [\#44](https://github.com/Cadasta/cadasta-platform/issues/44)
- Archive/unarchive projects [\#38](https://github.com/Cadasta/cadasta-platform/issues/38)
- Project serializer [\#36](https://github.com/Cadasta/cadasta-platform/issues/36)
- Design project API [\#35](https://github.com/Cadasta/cadasta-platform/issues/35)
- Permissions for projects [\#34](https://github.com/Cadasta/cadasta-platform/issues/34)
- Project model [\#33](https://github.com/Cadasta/cadasta-platform/issues/33)
- Ansible error on startup [\#32](https://github.com/Cadasta/cadasta-platform/issues/32)
- Permissions system [\#26](https://github.com/Cadasta/cadasta-platform/issues/26)
- Form field validation [\#23](https://github.com/Cadasta/cadasta-platform/issues/23)
- Searchable/Sortable/Filterable Lists [\#20](https://github.com/Cadasta/cadasta-platform/issues/20)
- Reusable components [\#19](https://github.com/Cadasta/cadasta-platform/issues/19)
- Resources [\#15](https://github.com/Cadasta/cadasta-platform/issues/15)
- Fixed user roles and permissions [\#8](https://github.com/Cadasta/cadasta-platform/issues/8)
- Users/Login/Registration [\#7](https://github.com/Cadasta/cadasta-platform/issues/7)

**Merged pull requests:**

- added drf docs [\#108](https://github.com/Cadasta/cadasta-platform/pull/108) ([ian-ross](https://github.com/ian-ross))
- Cleanup/projects roles api [\#106](https://github.com/Cadasta/cadasta-platform/pull/106) ([ian-ross](https://github.com/ian-ross))
- edited project views [\#105](https://github.com/Cadasta/cadasta-platform/pull/105) ([eomwandho](https://github.com/eomwandho))
- Created management command 'loadfixtures' [\#104](https://github.com/Cadasta/cadasta-platform/pull/104) ([linzjax](https://github.com/linzjax))
- Upgrades, translations, test infrastructure [\#101](https://github.com/Cadasta/cadasta-platform/pull/101) ([ian-ross](https://github.com/ian-ross))
- Implements FieldSelectorSerializer [\#100](https://github.com/Cadasta/cadasta-platform/pull/100) ([oliverroick](https://github.com/oliverroick))
- User management API [\#97](https://github.com/Cadasta/cadasta-platform/pull/97) ([ian-ross](https://github.com/ian-ross))
- First cut at permissions policies [\#88](https://github.com/Cadasta/cadasta-platform/pull/88) ([ian-ross](https://github.com/ian-ross))
- Update for new tutelary functionality [\#87](https://github.com/Cadasta/cadasta-platform/pull/87) ([ian-ross](https://github.com/ian-ross))
- Footer & Footer CSS [\#85](https://github.com/Cadasta/cadasta-platform/pull/85) ([clash99](https://github.com/clash99))
- Functional testing [\#79](https://github.com/Cadasta/cadasta-platform/pull/79) ([ian-ross](https://github.com/ian-ross))
- Implements form field validation for user accounts [\#77](https://github.com/Cadasta/cadasta-platform/pull/77) ([oliverroick](https://github.com/oliverroick))
- Add version to API URL in front-end [\#74](https://github.com/Cadasta/cadasta-platform/pull/74) ([ian-ross](https://github.com/ian-ross))
- Remove "http://" from api\_url in vagrant.yml [\#73](https://github.com/Cadasta/cadasta-platform/pull/73) ([ian-ross](https://github.com/ian-ross))
- DRY-out web pack config [\#72](https://github.com/Cadasta/cadasta-platform/pull/72) ([oliverroick](https://github.com/oliverroick))
- Install git when provisioning VM [\#71](https://github.com/Cadasta/cadasta-platform/pull/71) ([oliverroick](https://github.com/oliverroick))
- Adds organization models, serializer and views [\#64](https://github.com/Cadasta/cadasta-platform/pull/64) ([oliverroick](https://github.com/oliverroick))
- Css for User Pages [\#63](https://github.com/Cadasta/cadasta-platform/pull/63) ([clash99](https://github.com/clash99))
- Better Webpack configuration [\#60](https://github.com/Cadasta/cadasta-platform/pull/60) ([ian-ross](https://github.com/ian-ross))
- Changes for deployment to AWS [\#58](https://github.com/Cadasta/cadasta-platform/pull/58) ([ian-ross](https://github.com/ian-ross))
- Create LICENSE [\#6](https://github.com/Cadasta/cadasta-platform/pull/6) ([oliverroick](https://github.com/oliverroick))
- Internationalisation [\#5](https://github.com/Cadasta/cadasta-platform/pull/5) ([oliverroick](https://github.com/oliverroick))
- Initial front-end setup and user authentication flows [\#3](https://github.com/Cadasta/cadasta-platform/pull/3) ([oliverroick](https://github.com/oliverroick))
- Travis setup + Vagrant update [\#2](https://github.com/Cadasta/cadasta-platform/pull/2) ([oliverroick](https://github.com/oliverroick))
- Add RandomIDModel [\#1](https://github.com/Cadasta/cadasta-platform/pull/1) ([oliverroick](https://github.com/oliverroick))
