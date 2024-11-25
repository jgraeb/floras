# Package Delivery Example

![package delivery sim](packagedeliverysim.gif)

The system under test is the robot moving on the grid, its objective is to delivery all five packages (the order does not matter) and then reach its target location on the left edge of the grid (orange). The robot can only carry maximum one package at once, therefore it cannot move through a state with a package while it is already carrying another package.
The test objective is that the packages are to be delivered in a specific order, namely $p_5,p_4,p_3,p_2,p_1$.

The black barriers are found by the flow-based reactive test synthesis framework and ensure that the robot has to deliver the packages in the desired order.

The code for this example can be found in [this repo](https://github.com/jgraeb/floras/tree/main/case_studies/package_delivery).