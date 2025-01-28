# Package Delivery Example

![package delivery sim](packagedeliverysim.gif)

The system under test is the robot moving on the grid. Its objective is to delivery all five packages to their goal location (shaded in the same color). The order of delivery does not matter to the robot. Finally, it needs to reach its target location on the left edge of the grid (orange).
The robot can only carry at maximum one package at once. Therefore, it cannot move through a state containing a package while it is already carrying another package. It can only drop the packages off at the corresponding target location or back at the pickup location.
The test objective is that the packages are to be delivered in a specific order, namely $p_5,p_4,p_3,p_2,p_1$.

The black barriers are found by the flow-based reactive test synthesis framework and ensure that the robot has to deliver the packages in the desired order. The framework finds this configuration with a flow of $F=2$.

The code for this example can be found in [this repo](https://github.com/jgraeb/floras/tree/main/case_studies/package_delivery).