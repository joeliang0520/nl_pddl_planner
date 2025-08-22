(define (problem problem_1)
    (:domain domain_1)
    
    (:objects
        r1 r2 r3 - receptacle
        o1 o2 - object
        p1 - potato
    )
    
    (:init
        (not (holdsAny))
    )
    
    (:goal
        (and
            (inReceptacle r1 p1)
            (isHot p1)
            (isPotato p1)
            (isTable r1)
            ;(isContained p1)
        )
    )
)