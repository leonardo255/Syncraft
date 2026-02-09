from langchain.tools import tool
import random
import simpy

@tool
def run_simulation(
    s: int,              # reorder point
    S: int,              # order-up-to level
) -> dict:
    """
    SimPy simulation of a single-product (s, S) inventory control system.

    The model:
    ----------
    - The simulation proceeds in discrete daily steps.
    - Daily customer demand is random.
    - If inventory falls to or below the reorder point `s`,
      an order is placed to raise inventory up to level `S`.
    - Orders arrive after a stochastic lead time.
    - Inventory can reach zero; shortages incur a cost.
    - Costs accumulate over the entire simulated horizon.
    - Costs are simulated in DKK

    Inventory policy:
    -----------------
    (s, S) policy:
        If inventory <= s:
            place an order of size (S - current_inventory)

    Returned metrics:
    -----------------
    A dictionary containing the following aggregated cost components:

    - total_cost:
        The sum of all cost types over the full simulation period:
        total_cost = holding_cost + ordering_cost + stockout_cost

    - holding_cost:
        Cost of keeping units in stock.
        Every day: holding_cost += inventory_level * holding_cost_per_unit.
        Encourages avoiding excessive inventory.

    - ordering_cost:
        Fixed cost incurred each time an order is placed.
        Represents administrative + shipping costs.
        Encourages placing fewer, larger orders.

    - stockout_cost:
        Penalty applied when demand exceeds available inventory.
        Models loss of goodwill, expedited shipments, or lost sales.
        Encourages keeping safety stock to avoid running out.

    - ending_inventory:
        The final on-hand inventory level at the end of the simulation.
        Useful for checking whether inventory levels drift upward
        or downward relative to the policy.

    Returns:
    --------
    dict: {
        "total_cost": float,
        "holding_cost": float,
        "ordering_cost": float,
        "stockout_cost": float,
        "ending_inventory": int
    }

    """

    days = 365
    demand_mean = 5     # avg daily demand (Poisson-like)
    lead_time_min = 2
    lead_time_max = 5
    holding_cost = 1.0
    order_cost = 20.0
    stockout_cost = 5.0
    seed = 1

    if seed is not None:
        random.seed(seed)


    print(f"Running simulation with s={s}, S={S}, seed={seed}")


    env = simpy.Environment()

    # State variables
    inventory = {"level": S}
    cost = {
        "holding": 0.0,
        "ordering": 0.0,
        "stockout": 0.0,
    }

    def generate_demand(mean):
        """Tiny Poisson-like generator without numpy."""
        # approximate Poisson by summing Bernoulli trials
        return sum(1 for _ in range(mean * 2) if random.random() < 0.5)

    def inventory_process(env, inventory, cost):
        on_order = 0
        arrival_event = None

        for day in range(days):
            # ---------------------------------------------------
            # 1. Check if scheduled replenishment arrives today
            # ---------------------------------------------------
            if arrival_event and arrival_event.triggered:
                inventory["level"] += on_order
                on_order = 0
                arrival_event = None

            # ---------------------------------------------------
            # 2. Demand realization
            # ---------------------------------------------------
            demand = generate_demand(demand_mean)
            if demand <= inventory["level"]:
                inventory["level"] -= demand
            else:
                shortage = demand - inventory["level"]
                inventory["level"] = 0
                cost["stockout"] += shortage * stockout_cost

            # ---------------------------------------------------
            # 3. Holding cost
            # ---------------------------------------------------
            cost["holding"] += inventory["level"] * holding_cost

            # ---------------------------------------------------
            # 4. Reorder decision (s, S)
            # ---------------------------------------------------
            if inventory["level"] <= s and on_order == 0:
                qty = S - inventory["level"]
                on_order = qty
                cost["ordering"] += order_cost

                # schedule arrival
                delay = random.randint(lead_time_min, lead_time_max)
                arrival_event = env.timeout(delay)

            # ---------------------------------------------------
            # 5. Advance one day
            # ---------------------------------------------------
            yield env.timeout(1)

    # Start the inventory process
    env.process(inventory_process(env, inventory, cost))

    # Run
    env.run()

    # Final output
    total_cost = cost["holding"] + cost["ordering"] + cost["stockout"]
    return {
        "total_cost": total_cost,
        "holding_cost": cost["holding"],
        "ordering_cost": cost["ordering"],
        "stockout_cost": cost["stockout"],
        "ending_inventory": inventory["level"]
    }


# ----------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------
if __name__ == "__main__":
    result = run_simulation(s=20, S=50)
    print(result)