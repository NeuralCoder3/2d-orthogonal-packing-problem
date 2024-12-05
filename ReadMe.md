# 2D-Optimal-Orthogonal-Packing

We want to place a bunch of rectangles into a larger one (the bin).
The 2d optimal orthogonal packing (OOP) problem is closely related to bin packing.

OOP is known to be NP-hard. However, approximation algorithms exists.
Usual approaches place the bins in each dimension separately while trying to satisfy 
the remaining constraints.
An example is given in "A new search procedure for the two-dimensional orthogonal
packing problem" by Grandcolas and Pinto based on "A new exact method for the two-dimensional orthogonal packing problem"
by Clautiaux et al.

Instead, we use constraint programming/smt solvers to find a satisfactory assignment.
In that, we have a few simple constraints:
- 0 <= xi < W /\\ 0 <= yi < H for all rectangles i
  (Coordinates in bounds)
- i != j ->
  xi+wi <= xj \\/ xj+wj<= xi \\/ yi+hi <= yj \\/ yj+hj <= yi
  (No overlap between images)