# Part 1 – Multiple Choice Questions:
     
# 1. b) @api.depends
# 2. c) Access control lists (ACLs)
# 3. d) Selection
# 4. a) mail.thread


# Part 2 – Short Answer Questions :

# 1. Explain the difference between related fields and computed fields in Odoo.
#    Related fields are fields that fetch their value from another model's field, creating a direct link between models. 
#    Computed fields, on the other hand, derive their value from a method defined in the model and can involve complex calculations. it use @api.depends decorator to specify dependencies.

# 2. What is the role of Record Rules compared to Access Rights?
#  Record rules define record what specific user can access based on certain criteria,
#  while acess rights determine what actions (read, write, create, delete) a user can perform on a model.
 
#  3. What is the return of some orm method add any 5 orm return.
#  few orm method return type are:
# write: Boolean
# create: Recordset
# search_count: Integer
# unlink :deleted records
# read: List of dictionaries
# search: Recordset

#  4.Define the purpose of @api.onchange and give a practical example.
#   @api.onchange is used trigger method when any field value is change in form view.
# example: it is used in exam dashboard model to save last selected course filter.
    # @api.onchange('course_filter')
    # def _onchange_course_filter(self):
    #     if self.course_filter:
    #         self.env['ir.default'].set('exam.dashboard', 'course_filter', self.course_filter, self.env.uid)
    
# 5.Explain the difference between search and browse methods..
#  Search method is used to find a recordset based on specific criteria and returns a recordset of matching records.
#  while Browse method is used to acess record directly by their id and return a recordset of those record.

