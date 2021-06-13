import pytest

import numpy           as np
import jax.numpy       as jnp
import statsmodels.api as sm

from itea.classification import ITExpr_classifier,ITEA_classifier

from jax import grad, vmap

from sklearn.datasets   import make_blobs
from sklearn.exceptions import NotFittedError
from sklearn.base       import clone


# Using the identity, one trigonometric and one non-linear function
tfuncs = {
    'id'       : lambda x: x,
    'sin'      : jnp.sin,
    'sqrt.abs' : lambda x: jnp.sqrt(jnp.abs(x)), 
}

# analitically calculated derivatives
tfuncs_dx = {
    'sin'      : np.cos,
    'sqrt.abs' : lambda x: x/( 2*(np.abs(x)**(3/2)) ),
    'id'       : lambda x: np.ones_like(x),
}

# Automatic differentiation derivatives
tfuncs_dx_jax = {k : vmap(grad(v)) for k, v in tfuncs.items()}


@pytest.fixture
def classification_toy_data():
    return make_blobs(
        n_samples    = 100,
        n_features   = 2,
        cluster_std  = 1,
        centers      = [(-10,-10), (0,0), (10, 10)], # 3 classes
        random_state = 0,
    )

@pytest.fixture
def linear_ITExpr():
    """Linear IT expresison that should fit perfectly to the toy data set.
    
    The ITExpr has no explicit labels in this case.
    """

    return ITExpr_classifier(
        expr = [
            ('id', [1, 0]),
            ('id', [0, 1]),
        ],
        tfuncs = tfuncs
    )

@pytest.fixture
def nonlinear_ITExpr():
    """non linear expression."""

    return ITExpr_classifier(
        expr = [
            ('sin',      [0, -1]),
            ('sqrt.abs', [1,  1]),
        ],
        tfuncs = tfuncs,
    )


def test_initial_state(linear_ITExpr):

    assert linear_ITExpr._is_fitted == False
    assert linear_ITExpr._fitness   == np.inf

    assert not hasattr(linear_ITExpr, 'coef_')
    assert not hasattr(linear_ITExpr, 'intercept_')
    assert not hasattr(linear_ITExpr, 'classes_')


def test_linear_ITExpr_evaluation(
    linear_ITExpr, classification_toy_data):

    X, y = classification_toy_data
    
    assert np.allclose(X, linear_ITExpr._eval(X))


def test_linear_ITExpr_fit(
    linear_ITExpr, classification_toy_data):

    X, y = classification_toy_data

    with pytest.raises(NotFittedError):
        linear_ITExpr.predict(X)

    with pytest.raises(NotFittedError):
        linear_ITExpr.predict_proba(X)

    linear_ITExpr.fit(X, y)

    assert np.array(linear_ITExpr.coef_).ndim == 2
    assert np.array(linear_ITExpr.intercept_).ndim == 1
    assert linear_ITExpr.classes_ == [0, 1, 2]

    # Shoudnt raise an error anymore    
    linear_ITExpr.predict(X)

    # The ITExpr is exactly the same original expresison. must have almost
    # perfect results.
    assert np.isclose(linear_ITExpr._fitness, 1.0)


def test_linear_ITExpr_predict(
    linear_ITExpr, classification_toy_data):

    X, y = classification_toy_data

    assert np.allclose(linear_ITExpr.fit(X, y).predict(X), y)


def test_linear_ITExpr_predict_proba(
    linear_ITExpr, classification_toy_data):

    X, y = classification_toy_data

    probas = linear_ITExpr.fit(X, y).predict_proba(X)
    for p, yi in zip(probas, y):
        assert np.argmax(p) == yi


def test_nonlinear_ITExpr_derivatives_with_jax(
    nonlinear_ITExpr, classification_toy_data):

    X, y = classification_toy_data

    assert np.allclose(
        nonlinear_ITExpr.gradient(X, tfuncs_dx, logit=True),
        nonlinear_ITExpr.gradient(X, tfuncs_dx_jax, logit=True)
    )


def test_ITEA_classifier_fit_predict(classification_toy_data):
    X, y = classification_toy_data

    clf = ITEA_classifier(
        gens=10, popsize=10, verbose=2, random_state=42).fit(X, y)

    # The fitness and bestsol attributes should exist after fit
    assert hasattr(clf, 'bestsol_')
    assert hasattr(clf, 'fitness_')
    assert hasattr(clf, 'classes_')

    # Those atributes should be shared between the ITEA and best ITExpr
    # (fitness is private for ITExpr. It is not created only after fitting
    # the model and has meaning on the evolution context. The ITEA have the 
    # fitness_ attribute for convenience. Idealy (like any other scikit model),
    # the score() is implemented to assess the model performance.)

    assert clf.fitness_ == clf.bestsol_._fitness
    assert np.allclose(clf.score(X, y), clf.bestsol_.score(X, y))

    # predict() called on ITEA or ITExpr always corresponds to calling it
    # directly on the ITExpr
    assert np.allclose(clf.predict(X), clf.bestsol_.predict(X))