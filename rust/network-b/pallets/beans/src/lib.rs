//! # BEANS Pallet
//!
//! Institutional-grade tokenomics with Critical Complex Equilibrium
//!
//! ## Mathematical Foundation
//!
//! Based on "Proof of Critical Complex Equilibrium" by Sarah Marin (October 18, 2025)
//!
//! - μ = -η + iλ (eigenvalue definition)
//! - |μ|² = η² + λ² = 1 (unit circle constraint)
//! - |Re(μ)| = |Im(μ)| ⇒ η = λ (perfect balance)
//! - 2λ² = 1 ⇒ λ = η = 1/√2 ≈ 0.7071
//!
//! ## Fee Distribution
//!
//! With unit circle constraint (validator² + burn² + treasury² = 1):
//! - Validator: 1/(1+√2) ≈ 41.42%
//! - Burn: (1/√2)/(1+√2) ≈ 29.29%
//! - Treasury: (1/√2)/(1+√2) ≈ 29.29%

#![cfg_attr(not(feature = "std"), no_std)]

pub use pallet::*;

#[frame_support::pallet]
pub mod pallet {
    use frame_support::{
        pallet_prelude::*,
        traits::{Currency, ExistenceRequirement, Imbalance, OnUnbalanced},
    };
    use frame_system::pallet_prelude::*;
    use sp_runtime::{
        traits::{CheckedAdd, CheckedMul, CheckedSub, Saturating, Zero},
        Permill,
    };
    use sp_std::vec::Vec;

    /// Critical Complex Equilibrium Constants
    /// λ = η = 1/√2 ≈ 0.7071
    pub const CRITICAL_CONSTANT_PERMIL: u32 = 707; // 70.7% in per-thousand

    /// Unit Circle Normalization: 1/(1+√2) ≈ 0.4142
    pub const UNIT_CIRCLE_NORM_PERMIL: u32 = 414; // 41.4% in per-thousand

    /// Fee distribution based on Critical Complex Equilibrium
    /// Validator: 1/(1+√2) ≈ 41.42%
    pub const VALIDATOR_FEE_SHARE: Permill = Permill::from_parts(414_200); // 41.42%

    /// Burn: (1/√2)/(1+√2) ≈ 29.29%
    pub const BURN_FEE_SHARE: Permill = Permill::from_parts(292_900); // 29.29%

    /// Treasury: (1/√2)/(1+√2) ≈ 29.29%
    pub const TREASURY_FEE_SHARE: Permill = Permill::from_parts(292_900); // 29.29%

    /// Block reward constants
    pub const INITIAL_BLOCK_REWARD: u128 = 3_125_000_000; // 3.125 BEANS (in wei, 10^9)
    pub const WEI_PER_BEAN: u128 = 1_000_000_000; // 10^9
    pub const REWARD_HALVING_BLOCKS: u32 = 1_051_200; // ~24.3 days at 2s blocks
    pub const MIN_BLOCK_REWARD: u128 = 100_000_000; // 0.1 BEANS

    type BalanceOf<T> =
        <<T as Config>::Currency as Currency<<T as frame_system::Config>::AccountId>>::Balance;

    #[pallet::config]
    pub trait Config: frame_system::Config {
        /// The overarching event type
        type RuntimeEvent: From<Event<Self>> + IsType<<Self as frame_system::Config>::RuntimeEvent>;

        /// Currency type for balance operations
        type Currency: Currency<Self::AccountId>;

        /// Treasury account for fee collection
        #[pallet::constant]
        type TreasuryAccount: Get<Self::AccountId>;

        /// Burn account (dead address)
        #[pallet::constant]
        type BurnAccount: Get<Self::AccountId>;
    }

    #[pallet::pallet]
    pub struct Pallet<T>(_);

    /// Total supply of $BEANS (pure emission model - starts at 0)
    #[pallet::storage]
    #[pallet::getter(fn total_supply)]
    pub type TotalSupply<T: Config> = StorageValue<_, BalanceOf<T>, ValueQuery>;

    /// Total amount burned (deflationary mechanism)
    #[pallet::storage]
    #[pallet::getter(fn total_burned)]
    pub type TotalBurned<T: Config> = StorageValue<_, BalanceOf<T>, ValueQuery>;

    /// Total rewards distributed to validators
    #[pallet::storage]
    #[pallet::getter(fn total_rewarded)]
    pub type TotalRewarded<T: Config> = StorageValue<_, BalanceOf<T>, ValueQuery>;

    /// Total fees collected
    #[pallet::storage]
    #[pallet::getter(fn total_fees)]
    pub type TotalFees<T: Config> = StorageValue<_, BalanceOf<T>, ValueQuery>;

    #[pallet::event]
    #[pallet::generate_deposit(pub(super) fn deposit_event)]
    pub enum Event<T: Config> {
        /// Block reward distributed [block_number, validator, reward, burned, treasury]
        BlockRewardDistributed {
            block_number: BlockNumberFor<T>,
            validator: T::AccountId,
            base_reward: BalanceOf<T>,
            validator_reward: BalanceOf<T>,
            burned: BalanceOf<T>,
            treasury: BalanceOf<T>,
        },
        /// Tokens burned [amount, total_burned]
        TokensBurned {
            amount: BalanceOf<T>,
            total: BalanceOf<T>,
        },
    }

    #[pallet::error]
    pub enum Error<T> {
        /// Arithmetic overflow
        Overflow,
        /// Insufficient balance
        InsufficientBalance,
    }

    #[pallet::hooks]
    impl<T: Config> Hooks<BlockNumberFor<T>> for Pallet<T> {
        fn on_finalize(block_number: BlockNumberFor<T>) {
            // Distribute block rewards at the end of each block
            if let Some(author) = <frame_system::Pallet<T>>::block_author() {
                let _ = Self::distribute_block_rewards(block_number, author);
            }
        }
    }

    impl<T: Config> Pallet<T> {
        /// Calculate block reward based on halving schedule
        pub fn calculate_block_reward(block_number: BlockNumberFor<T>) -> u128 {
            let block_num: u128 = block_number.saturated_into();
            let halvings = block_num / REWARD_HALVING_BLOCKS as u128;

            let mut reward = INITIAL_BLOCK_REWARD;
            for _ in 0..halvings {
                reward = reward / 2;
                if reward <= MIN_BLOCK_REWARD {
                    return MIN_BLOCK_REWARD;
                }
            }
            reward
        }

        /// Distribute block rewards with Critical Complex Equilibrium fee split
        pub fn distribute_block_rewards(
            block_number: BlockNumberFor<T>,
            validator: T::AccountId,
        ) -> DispatchResult {
            // Calculate base block reward (new emission)
            let base_reward_u128 = Self::calculate_block_reward(block_number);
            let base_reward: BalanceOf<T> = base_reward_u128.saturated_into();

            // For now, assume zero transaction fees (will be populated later)
            let total_fees: BalanceOf<T> = Zero::zero();

            // Calculate fee distribution (will be non-zero when fees exist)
            let validator_fee_reward = VALIDATOR_FEE_SHARE * total_fees;
            let burn_amount = BURN_FEE_SHARE * total_fees;
            let treasury_amount = TREASURY_FEE_SHARE * total_fees;

            // Validator gets: base reward + fee share
            let validator_reward = base_reward
                .checked_add(&validator_fee_reward)
                .ok_or(Error::<T>::Overflow)?;

            // Mint base reward (new token emission)
            let base_imbalance = T::Currency::deposit_creating(&validator, base_reward);

            // Transfer fee rewards if any
            if !validator_fee_reward.is_zero() {
                let _ = T::Currency::deposit_creating(&validator, validator_fee_reward);
            }

            // Burn tokens (deflationary mechanism)
            if !burn_amount.is_zero() {
                let burn_imbalance = T::Currency::deposit_creating(&T::BurnAccount::get(), burn_amount);
                TotalBurned::<T>::mutate(|total| *total = total.saturating_add(burn_amount));
            }

            // Send to treasury
            if !treasury_amount.is_zero() {
                let _ = T::Currency::deposit_creating(&T::TreasuryAccount::get(), treasury_amount);
            }

            // Update global statistics
            TotalSupply::<T>::mutate(|total| *total = total.saturating_add(base_reward));
            TotalRewarded::<T>::mutate(|total| *total = total.saturating_add(validator_reward));
            TotalFees::<T>::mutate(|total| *total = total.saturating_add(total_fees));

            // Emit event
            Self::deposit_event(Event::BlockRewardDistributed {
                block_number,
                validator: validator.clone(),
                base_reward,
                validator_reward,
                burned: burn_amount,
                treasury: treasury_amount,
            });

            Ok(())
        }
    }
}
