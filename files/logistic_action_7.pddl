(define (domain logistics-strips)
    (:requirements :strips :typing)
    (:types
        truck1 - truck
        truck2 - truck
        truck3 - truck
        truck4 - truck
        truck5 - truck
        truck6 - truck
        truck7 - truck
        obj truck airplane city airport loc
    ) ; default object

    (:predicates
        (at ?obj - obj ?loc - loc)
        (in ?obj1 - obj ?obj2 - obj)
    )

    (:action LOAD-TRUCK1
        :parameters (?obj - obj ?truck - truck1 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK1
        :parameters (?obj - obj ?truck - truck1 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK1
        :parameters (?truck - truck1 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
    (:action LOAD-TRUCK2
        :parameters (?obj - obj ?truck - truck2 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK2
        :parameters (?obj - obj ?truck - truck2 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK2
        :parameters (?truck - truck2 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
    (:action LOAD-TRUCK3
        :parameters (?obj - obj ?truck - truck3 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK3
        :parameters (?obj - obj ?truck - truck3 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK3
        :parameters (?truck - truck3 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
    (:action LOAD-TRUCK4
        :parameters (?obj - obj ?truck - truck4 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK4
        :parameters (?obj - obj ?truck - truck4 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK4
        :parameters (?truck - truck4 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
    (:action LOAD-TRUCK5
        :parameters (?obj - obj ?truck - truck5 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK5
        :parameters (?obj - obj ?truck - truck5 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK5
        :parameters (?truck - truck5 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
    (:action LOAD-TRUCK6
        :parameters (?obj - obj ?truck - truck6 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK6
        :parameters (?obj - obj ?truck - truck6 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK6
        :parameters (?truck - truck6 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
    (:action LOAD-TRUCK7
        :parameters (?obj - obj ?truck - truck7 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK7
        :parameters (?obj - obj ?truck - truck7 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK7
        :parameters (?truck - truck7 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
)