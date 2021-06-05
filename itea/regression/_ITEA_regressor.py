# Author:  Guilherme Aldeia
# Contact: guilherme.aldeia@ufabc.edu.br
# Version: 1.0.0
# Last modified: 05-30-2021 by Guilherme Aldeia


"""Specialization of the base class BaseITEA for the classification task.
"""


from sklearn.base             import RegressorMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted

from itea._base      import BaseITEA
from itea.regression import ITExpr_regressor


class ITEA_regressor(BaseITEA, RegressorMixin):
    """This is the implementation of the ITEA for the regression task.

    The expressions will have their coefficients adjusted by means of the
    scikit's linearRegression method. The fitness will be measured using
    the RMSE metric (smaller is better).
    """    
    
    def __init__(self, *, 
        gens            = 100,
        popsize         = 100, 
        tfuncs          = {'id': lambda x: x},
        tfuncs_dx       = None,
        expolim         = (-2, 2),
        max_terms       = 5,
        simplify_method = 'simplify_by_coef', 
        random_state    = None,
        verbose         = None,
        labels          = [],
        **kwargs
    ):
        """Constructor method.

        Parameters
        ----------

        gens : int, default=100
            number of generations of the evolutionary process.

        popsize : int, default=100
            population size, consistent through each generation.

        expolim : tuple (int, int), default = (-2, 2)
            tuple specifying the bounds of exponents for ITExpr.

        max_terms : int, default=5
            the max number of IT terms allowed.

        simplify_method : string or None, default=None
            String with the name of the simplification method to be used.
            When set to None, the simplification step is disabled.

        random_state : int, None or numpy.random_state, default=None
            int or numpy random state. When None, a random state instance
            will be created and used.

        verbose : int, None or False, default=None
            When verbose is None, False or 0, the algorithm
            will not print informations. If verbose is an integer
            ``n``, then every ``n`` generations the algorithm will
            print the status of the generation. If verbose is set
            to -1, every generation will print informations.

        labels : list of strings, default=[]
            (``ITExpr`` parameter) list containing the labels of the
            data that will be used in the evolutionary process, and
            will be used in ``ITExpr`` constructors.

        tfuncs : dict, default={'id': lambda x: x}
            (``ITExpr`` parameter) transformations functions. Should always
            be a dict where the keys are the names of the transformation
            functions and the values are unary vectorized functions.

        tfuncs_dx : dict, default=None
            (ITExpr_explainer parameter) derivatives of the
            given transformations functions, the same scheme.
            When set to None, the itea package will use automatic
            differentiation  through jax to create the derivatives.

        
        Attributes
        ----------

        bestsol_ : ITExpr_regressor
            an ITExpr expression used as it is (linear combination of IT terms).

        fitness_ : float
            fitness (RMSE) of the final expression.

        convergence_ : dict
            two nested dictionaries. The outer have the keys 
            ``['fitness', 'n_terms', 'complexity']``, and the inner 
            have ``['min', 'mean', 'std', 'max']``. Each value of the inner
            dictionary (for example itea.convergence_['fitness']['min'])
            is a list, containing the information of every generation.
            This dictionary can be used to inspect informations about the
            convergence of the evolutionary process.

        exectime_ : int
            time (in seconds) the evolutionary process took.
        """
                
        super(ITEA_regressor, self).__init__(
            gens            = gens, 
            popsize         = popsize,
            tfuncs          = tfuncs,
            tfuncs_dx       = tfuncs_dx,
            expolim         = expolim,
            max_terms       = max_terms,
            simplify_method = simplify_method, 
            random_state    = random_state,
            verbose         = verbose,
            labels          = labels)

        self.itexpr_class      = ITExpr_regressor
        self.greater_is_better = False


    def _check_args(self, X, y):
        """Argument verifications to be called before starting the evolutionary
        process.

        Since there is no logic on the constructor, and dealing with a 
        population of expressions makes the check infeasible within ITExpr
        methods, the check should be performed before the evolution.

        Should interrupt the program flow if any problem is found.
        """

        super()._check_args(X, y)


    def fit(self, X, y):
        """Performs the evolutionary process.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            training data.

        y : array-like of shape (n_samples, )
            expected values. 

        Returns
        -------
        self : ITEA_regressor
            itea after performing the evolution.
            Only after fitting the model that the attributes ``bestsol_`` and
            ``fitness_`` will be available.

        Raises
        ------
            ValueError
                If one or more arguments would result in a invalid execution of
                itea.
        """
        
        X, y = check_X_y(X, y)
        
        self._check_args(X, y)

        self.bestsol_ = self._evolve(
            X, y, self.itexpr_class, self.greater_is_better)
        
        self._fitness = self.bestsol_._fitness

        self._explain_bestsol(self.bestsol_, X, y)

        return self


    def predict(self, X):
        """Predicts the response value for each sample in X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            samples to be predicted. Must be a two-dimensional array.

        Returns
        -------
        p : numpy.array of shape (n_samples, )
            predicted response value for each sample.
        """

        check_is_fitted(self)

        X = check_array(X)

        return self.bestsol_.predict(X)