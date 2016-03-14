# simphony-metadata
This repository contains the metadata defnitions used in SimPhoNy project.


Repository

Simphony-metadata is hosted on github: https://github.com/simphony/simphony-metadata


Any all caps entity without the "CUBA." prefix, is being defined.  Any
all caps entity that has a "CUBA." prefix is assumed to be already
defined and it is being used.

The PARENT relation is an explicit inheritance of data! It defines
specific first order relations between data entities. The parent is
used in the same context as type in OO programming. Parent indicates a
directional first order relation.

CUBA.KEY (KEY can be any CUBA key) are attributes intrinsic to the
data entity defined.

Each CUBA.KEY has its own definition as an entity, which defines its
type (parent) in a unique universal manner.

Each CUBA.KEY can have additional implementation-related metadata,
these metadata are the following:

- default: a default value. When absent, no default is implied and the
  user has to eventually supply a value (not necessarily upon
  instantiation, implementation dependent).
 
- scope: CUBA.USER or CUBA.SYSTEM.  if omitted, CUBA.USER is
  assumed by default

- shape: [i_min:i_max,j_min:j_max] specifying that it is a
   multidimensional sequence of entities of its own type.  In each
   dimension, the first index is the minimum while the second the
   maximum number of items allowed.  An empty [] means no bounds are
   imposed but the value of the entity is an array, i.e., a sequence.
   Omitting lower or upper index means there is no corresponding
   limit.  e.g., [:10] it can have zero up to a maximum of 10
   allowed items. [2] means exactly 2 elements are allowed,
   equivalent to [2:2].  [2:] means minimum of 2 elements are
   allowed.


