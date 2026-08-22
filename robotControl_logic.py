"""
AliXRobot Mathematical Transformation Layer
============================================

Pure-Python 2D/3D homogeneous transformation utilities.

This module contains no PyQt6, PyQtGraph, or GUI code.

Responsibilities
----------------
- Parse numeric vectors
- Create identity matrices
- Multiply matrices
- Create translation matrices
- Create scaling matrices
- Create 2D rotation matrices
- Create 3D rotation matrices
- Compose transformations
- Transform points
"""

from __future__ import annotations

import ast
import math
from typing import Sequence


Matrix = list[list[float]]


# =========================================================
# INPUT PARSING
# =========================================================

def parse_numbers(
    text: str,
    expected_length: int | None = None,
) -> list[float]:
    """
    Safely parse a numerical list.

    Examples
    --------
    "[1, 2]" -> [1.0, 2.0]

    "[1, 2, 3]" -> [1.0, 2.0, 3.0]
    """

    if not isinstance(text, str):
        raise ValueError(
            "Input must be text."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "Input cannot be empty."
        )

    try:

        values = ast.literal_eval(text)

    except (
        SyntaxError,
        ValueError,
    ) as error:

        raise ValueError(
            "Use a numeric list, for example [1, 2, 3]."
        ) from error

    if not isinstance(
        values,
        (list, tuple),
    ):

        raise ValueError(
            "The value must be a list of numbers."
        )

    if not all(
        isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
        for value in values
    ):

        raise ValueError(
            "The value must contain only numbers."
        )

    if expected_length is not None:

        if len(values) != expected_length:

            raise ValueError(
                f"Expected {expected_length} numbers, "
                f"received {len(values)}."
            )

    return [
        float(value)
        for value in values
    ]


# =========================================================
# IDENTITY MATRIX
# =========================================================

def identity(
    size: int,
) -> Matrix:
    """
    Create an identity matrix.
    """

    if size <= 0:

        raise ValueError(
            "Matrix size must be positive."
        )

    return [

        [

            1.0
            if row == col
            else 0.0

            for col in range(size)

        ]

        for row in range(size)
    ]


# =========================================================
# MATRIX MULTIPLICATION
# =========================================================

def multiply(
    left: Matrix,
    right: Matrix,
) -> Matrix:
    """
    Multiply two matrices.
    """

    if not left or not right:

        raise ValueError(
            "Matrices cannot be empty."
        )

    if any(
        len(row) != len(left[0])
        for row in left
    ):

        raise ValueError(
            "Left matrix must be rectangular."
        )

    if any(
        len(row) != len(right[0])
        for row in right
    ):

        raise ValueError(
            "Right matrix must be rectangular."
        )

    if len(left[0]) != len(right):

        raise ValueError(
            "Matrices have incompatible dimensions."
        )

    return [

        [

            sum(
                left[row][k]
                *
                right[k][col]

                for k in range(
                    len(right)
                )
            )

            for col in range(
                len(right[0])
            )

        ]

        for row in range(
            len(left)
        )
    ]


# =========================================================
# TRANSLATION
# =========================================================

def translation(
    vector: Sequence[float],
) -> Matrix:
    """
    Create a homogeneous translation matrix.

    Supports 2D and 3D.
    """

    dimension = len(vector)

    if dimension not in (2, 3):

        raise ValueError(
            "Translation vectors must have "
            "two or three values."
        )

    result = identity(
        dimension + 1
    )

    for index, value in enumerate(vector):

        result[index][-1] = float(
            value
        )

    return result


# =========================================================
# SCALING
# =========================================================

def scaling(
    factors: float | Sequence[float],
    dimension: int,
) -> Matrix:
    """
    Create a homogeneous scaling matrix.

    A single number produces uniform scaling.

    Example
    -------
    scaling(2, 2)

    scales both x and y by 2.
    """

    if dimension not in (2, 3):

        raise ValueError(
            "Dimension must be 2 or 3."
        )

    if isinstance(
        factors,
        (int, float),
    ):

        factors = [
            float(factors)
        ] * dimension

    if len(factors) != dimension:

        raise ValueError(
            f"Expected {dimension} scale factors."
        )

    result = identity(
        dimension + 1
    )

    for index, value in enumerate(
        factors
    ):

        result[index][index] = float(
            value
        )

    return result


# =========================================================
# 2D ROTATION
# =========================================================

def rotation_2d(
    angle_degrees: float,
) -> Matrix:
    """
    Create a 2D homogeneous rotation matrix.
    """

    angle = math.radians(
        float(angle_degrees)
    )

    cosine = math.cos(angle)
    sine = math.sin(angle)

    return [

        [
            cosine,
            -sine,
            0.0,
        ],

        [
            sine,
            cosine,
            0.0,
        ],

        [
            0.0,
            0.0,
            1.0,
        ],
    ]


# =========================================================
# 3D ROTATION
# =========================================================

def rotation_3d(
    angle_degrees: float,
    axis: str = "z",
) -> Matrix:
    """
    Create a 3D homogeneous rotation matrix.
    """

    angle = math.radians(
        float(angle_degrees)
    )

    cosine = math.cos(angle)
    sine = math.sin(angle)

    axis = str(
        axis
    ).lower().strip()

    matrices = {

        "x": [

            [
                1.0,
                0.0,
                0.0,
                0.0,
            ],

            [
                0.0,
                cosine,
                -sine,
                0.0,
            ],

            [
                0.0,
                sine,
                cosine,
                0.0,
            ],

            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
        ],

        "y": [

            [
                cosine,
                0.0,
                sine,
                0.0,
            ],

            [
                0.0,
                1.0,
                0.0,
                0.0,
            ],

            [
                -sine,
                0.0,
                cosine,
                0.0,
            ],

            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
        ],

        "z": [

            [
                cosine,
                -sine,
                0.0,
                0.0,
            ],

            [
                sine,
                cosine,
                0.0,
                0.0,
            ],

            [
                0.0,
                0.0,
                1.0,
                0.0,
            ],

            [
                0.0,
                0.0,
                0.0,
                1.0,
            ],
        ],
    }

    if axis not in matrices:

        raise ValueError(
            "3D rotation axis must be "
            "'x', 'y', or 'z'."
        )

    return [
        [
            float(value)
            for value in row
        ]
        for row in matrices[axis]
    ]


# =========================================================
# TRANSFORMATION COMPOSITION
# =========================================================

def compose_transform(
    dimension: int,
    translate_by: Sequence[float] | None = None,
    rotate_degrees: float | None = None,
    scale_by: float | Sequence[float] | None = None,
    axis: str = "z",
) -> Matrix:
    """
    Create a combined homogeneous transformation.

    The resulting transformation is:

        T × R × S

    Therefore a point is:

        1. scaled
        2. rotated
        3. translated
    """

    if dimension not in (2, 3):

        raise ValueError(
            "Dimension must be 2 or 3."
        )

    result = identity(
        dimension + 1
    )

    # -----------------------------------------------------
    # TRANSLATION
    # -----------------------------------------------------

    if translate_by is not None:

        if len(translate_by) != dimension:

            raise ValueError(
                f"Translation needs "
                f"{dimension} values."
            )

        result = multiply(

            translation(
                translate_by
            ),

            result,
        )

    # -----------------------------------------------------
    # ROTATION
    # -----------------------------------------------------

    if rotate_degrees is not None:

        if dimension == 2:

            rotation = rotation_2d(
                rotate_degrees
            )

        else:

            rotation = rotation_3d(
                rotate_degrees,
                axis,
            )

        result = multiply(
            result,
            rotation,
        )

    # -----------------------------------------------------
    # SCALING
    # -----------------------------------------------------

    if scale_by is not None:

        result = multiply(

            result,

            scaling(
                scale_by,
                dimension,
            ),
        )

    return result


# =========================================================
# TRANSFORM POINT
# =========================================================

def transform_point(
    point: Sequence[float],
    transform: Matrix,
) -> list[float]:
    """
    Apply a homogeneous transformation to a point.
    """

    dimension = len(point)

    if dimension not in (2, 3):

        raise ValueError(
            "Point must contain "
            "two or three coordinates."
        )

    if len(transform) != dimension + 1:

        raise ValueError(
            "Point and transformation "
            "dimensions do not match."
        )

    homogeneous = [

        [
            float(value)
        ]

        for value in point

    ] + [

        [1.0]

    ]

    result = multiply(
        transform,
        homogeneous,
    )

    w = result[-1][0]

    if math.isclose(
        w,
        0.0,
    ):

        raise ValueError(
            "Transformation produced "
            "an invalid homogeneous coordinate."
        )

    return [

        result[index][0] / w

        for index in range(
            dimension
        )
    ]