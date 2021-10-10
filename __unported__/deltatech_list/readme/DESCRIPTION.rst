Functions:
 - Keep selection after sorting
 - Display a legend button in the list view.  The legend is extracted from the action's help field if it contains a tag with id "legend".



Pentru adaugarea de butoane in header se adauga in contextul actiunii:
{  'general_buttons':  [  { 'action': "print_pdf", 'name': "Print Preview"}]}
