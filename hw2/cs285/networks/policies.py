import itertools
from torch import nn
from torch.nn import functional as F
from torch import optim

import numpy as np
import torch
from torch import distributions

from cs285.infrastructure import pytorch_util as ptu


class MLPPolicy(nn.Module):
    """Base MLP policy, which can take an observation and output a distribution over actions.

    This class should implement the `forward` and `get_action` methods. The `update` method should be written in the
    subclasses, since the policy update rule differs for different algorithms.
    """

    def __init__(
        self,
        ac_dim: int,
        ob_dim: int,
        discrete: bool,
        n_layers: int,
        layer_size: int,
        learning_rate: float,
    ):
        super().__init__()

        if discrete:
            self.logits_net = ptu.build_mlp(
                input_size=ob_dim,
                output_size=ac_dim,
                n_layers=n_layers,
                size=layer_size,
            ).to(ptu.device)
            parameters = self.logits_net.parameters()
        else:
            self.mean_net = ptu.build_mlp(
                input_size=ob_dim,
                output_size=ac_dim,
                n_layers=n_layers,
                size=layer_size,
            ).to(ptu.device)
            self.logstd = nn.Parameter(
                torch.zeros(ac_dim, dtype=torch.float32, device=ptu.device)
            )
            parameters = itertools.chain([self.logstd], self.mean_net.parameters())

        self.optimizer = optim.Adam(
            parameters,
            learning_rate,
        )

        self.discrete = discrete

    @torch.no_grad()
    def get_action(self, obs: np.ndarray) -> np.ndarray:
        """Takes a single observation (as a numpy array) and returns a single action (as a numpy array)."""
        # DONE: implement get_action
        obs = ptu.from_numpy(obs)
        dist = self(obs)
        action = dist.sample()

        return ptu.to_numpy(action)

    def forward(self, obs: torch.FloatTensor) -> torch.distributions.Distribution:
        """
        This function defines the forward pass of the network.  You can return anything you want, but you should be
        able to differentiate through it. For example, you can return a torch.FloatTensor. You can also return more
        flexible objects, such as a `torch.distributions.Distribution` object. It's up to you!
        """
        if self.discrete:
            # DONE: define the forward pass for a policy with a discrete action space.
            probs = self.logits_net(obs)
            action = torch.distributions.Categorical(logits=probs)
        else:
            # DONE: define the forward pass for a policy with a continuous action space.
            means = self.mean_net(obs)
            std = torch.exp(self.logstd)
            action = torch.distributions.Normal(means, std)
        return action

    def update(self, obs: np.ndarray, actions: np.ndarray, advantages: np.ndarray, *args, **kwargs) -> dict:
        """Performs one iteration of gradient descent on the provided batch of data."""
        raise NotImplementedError


class MLPPolicyPG(MLPPolicy):
    """Policy subclass for the policy gradient algorithm."""

    def update(
        self,
        obs: np.ndarray,
        actions: np.ndarray,
        advantages: np.ndarray,
        *args, **kwargs
    ) -> dict:
        """Implements the policy gradient actor update."""
        N = obs.shape[1]
        obs = ptu.from_numpy(obs)
        actions = ptu.from_numpy(actions)
        advantages = ptu.from_numpy(advantages)

        self.optimizer.zero_grad()

        dists: distributions.Distribution = self(obs)
        log_probs = dists.log_prob(actions)

        # print(f"log probs: {log_probs}, {log_probs.shape}")
        # print(f"advantages: {advantages}, {advantages.shape}")

        # DONE: implement the policy gradient actor update.
        loss = -(log_probs * advantages.unsqueeze(-1)).mean()

        loss.backward()
        self.optimizer.step()

        return {
            "Actor Loss": ptu.to_numpy(loss),
        }
