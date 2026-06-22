Frontend components needed:

NavBar
  The bar itself with a logo.
NavLink
  A link to a page with a CSS underline effect for use on the NavBar.
Footer
  The footer itself with static information (column names, copyrights)
NavBarAvatar
  A user's avatar for use on the NavBar with a dropdown menu for account settings, app settings, their dashboard, and help. Uses their profile picture in a circle.
PostCard
  The container for a Forum post itself, featuring a three-tier layout: poster information (avatar, name, subtitle/role), the post itself (text, image, video, composite), and then action buttons (like, repost, save).
NavSidebar
  A left-sidebar with repurposed NavLinks stacked vertically for quick navigation around settings menus, dashboards, etc.
CTASidebar
  A wider left-sidebar with a personalised and contextual welcome message (Good morning/afternoon <user>). Features two vertically-stacked AlbumCards, three horizontally-laid-out SnippetCards, and an AgentChat card at the bottom.
AlbumCard
  A wide card used to open an "Album", which can be thought of like a course, however these are informational and function by delivering information in bite-sized chunks (Snippets) which users can like or save each piece independently and gain XP for reading each piece. Features a square portion on the left like a SnippetCard with an icon, then in a second right-portion a title of the Album, a subtitle/slogan/cta, a progress-out-of indicator to show how many Snippets the user has read, and a progress bar in the same orange-yellow gradient that is used for the NavLinks.
SnippetCard
  A square card used to open a "Snippet", which is just a static article. Features a centered icon, and a title of the page under it.
AgentChat
  A rectangular field for users to chat with their personalised agent (the Dynamic Mentor), exists in plain white with an accent line along the bottom in the same orange-yellow universal gradient with CTA placeholder text where the user will type.
AlbumProgressWidget
  A widget that will be placed in the top-left corner of the screen of an Album which will hold the Album's title, and a smaller progress bar of that Album in the same orange-yellow gradient.
SnippetTitleBar
  A top titlebar shown on Snippets of the same height and flush with the AlbumProgressWidget which will display the current Snippet's title and have a dynamic progress bar along the bottom in the same orange-yellow as to the user's current reading progress of that Snippet.
AlbumSidebar
  An adapted version of the NavSidebar for Albums to display vertically-organised Sides (chapters) and their constituent Snippets.
UserProfileHeader
  A UserProfileHeader includes a background image, an avatar, a name, and a subtitle/role similar to a LinkedIn
UserProfileBio
  Contains pure text to be shown under the UserProfileHeader to contain a User's bio within 500 characters.
AudioPlayer
  A card-like component placed onto a Snippet for a spoken-audio version of the Snippet to be played. Can universally be activated by pressing a keybind, to help visually impaired users.
AlbumGrid
  A grid/list of AlbumCards used on the Album discovery page for browsing all available Albums (public, no account required to view).
SnippetGrid
  A grid/list of SnippetCards used for public browsing or search results of standalone Snippets.
SideHeader
  A divider/header shown inside an AlbumSidebar marking the start of a Side (chapter) and grouping its constituent Snippets underneath it.
EnrolButton
  A CTA button on an Album used to enrol in it. Prompts the login/registration flow if the user does not have an account.
LikeButton
  A reusable like control with a count, shared between PostCard and Snippets, used as a lightweight KPI for content popularity.
SaveButton
  A reusable save control shared between PostCard and Snippets, which adds the item to the user's personal Library.
XPBadge
  A small inline indicator showing the XP earned or available for reading a given Snippet, reinforcing the gamified progression loop.
LibraryShelf
  A grid/list of the user's saved Snippets, shown in The Library.
EnrolledAlbumsList
  A list of the user's enrolled AlbumCards with progress, shown in The Library.
ForumFeed
  A scrollable container of PostCards forming the main Forum feed view. Respects age-tier visibility rules.
PostComposer
  An input area for creating a new Post. Only rendered for users in the Career age tier (17+); access is enforced server-side regardless.
AgeGateNotice
  A banner shown in place of hidden social features for users under 16, explaining why those features are not yet available to them.
MentorBadge
  A small tag/label shown on a UserProfileHeader identifying accounts belonging to AWS mentors.
AgentChatWindow
  The full conversation history view for the Dynamic Mentor, as opposed to AgentChat which is just the input teaser shown in the CTASidebar.
SettingsNav
  A vertical nav, adapted from NavSidebar, for the Account Settings / App Settings pages reachable from the NavBarAvatar dropdown.
HelpPanel
  A content panel for the Help destination reachable from the NavBarAvatar dropdown.
