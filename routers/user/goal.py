from fastapi import APIRouter

from router_dependencies import *

router = APIRouter(tags=["Goals"])

@router.get("/{username}/goals")
def get_all_goals(username: str, db: Session = Depends(get_db), user: User = Security(get_authorized_user, scopes=['goals'])) -> list[resources.Goal]:
    check_username(username, user)
    return utils.get_user_goals(db, user)

@router.post("/{username}/goal/")
def add_new_goal(username: str, goal: resources.Goal, user: User = Security(get_authorized_user, scopes=['goals']), db: Session = Depends(get_db)) -> resources.Goal:
    check_username(username, user)
    g = utils.add_new_goal(
        db,
        user,
        goal.title,
        goal.status.to_integer(),
        start_datetime=goal.start_datetime,
        end_datetime=goal.end_datetime,
        average_target=goal.average_target,
        trend_target=goal.trend_target.to_integer(),
        stat_range=goal.stats_target.stat_range,
        minimum=goal.stats_target.minimum,
        maximum=goal.stats_target.maximum,
        mean=goal.stats_target.mean,
        median=goal.stats_target.median,
        first_quart=goal.stats_target.first_quartile,
        second_quart=goal.stats_target.second_quartile,
        third_quart=goal.stats_target.third_quartile,
        overall_samples_size=goal.stats_target.overall_samples_size,
        variance=goal.stats_target.variance,
        std_dev=goal.stats_target.standard_deviation
    )
    if not g:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Based on the title, goal already exists"
        )
    goal.id = g.id
    return goal

@router.delete("/{username}/goal/{id}")
def remove_goal(username: str, id: int, user: User = Security(get_authorized_user, scopes=['goals']), db: Session = Depends(get_db)) -> resources.Goal:
    check_username(username, user)
    g = utils.remove_goal(db, id)
    if not g:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="There is no goal with this identifier"
        )
    return g

@router.put("/{username}/goal/{id}")
def update_goal_element(username: str, id: int, updatedKey: resources.UpdatedKey, new_value: resources.GoalAttr, user: User = Security(get_authorized_user, scopes=['goals']), db: Session = Depends(get_db)) -> resources.Goal:
    check_username(username, user)
    g = utils.update_goal_attribute(db, id, updatedKey, new_value)
    if not g:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="There is no goal with this identifier"
        )
    return g